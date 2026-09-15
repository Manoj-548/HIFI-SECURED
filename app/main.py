from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Session as UserSession, User, UserPlan, UserSecurity
from app.schemas import ActivationRequest, GoogleLoginRequest, LoginResponse, UserResponse, Verify2FARequest
from app.security import (
    create_cookie_value,
    generate_refresh_token,
    generate_totp_secret,
    hash_value,
    is_plan_active,
    verify_totp,
)

MONTHLY_PLAN_PRICE_INR = 100
MONTHLY_PLAN_DAYS = 30

app = FastAPI(title="Token Secured", version="1.0.0")


def get_or_create_demo_user(db: Session) -> User:
    user = db.query(User).filter(User.email == "demo@example.com").first()
    if user:
        return user

    user = User(
        email="demo@example.com",
        google_user_id="demo-google-user",
        name="Demo User",
        email_verified=True,
        is_active=True,
        country="IN",
        timezone="Asia/Kolkata",
    )
    db.add(user)
    db.flush()

    security = UserSecurity(
        user_id=user.id,
        is_2fa_enabled=True,
        two_fa_method="totp",
        secret_key_encrypted=generate_totp_secret(),
    )
    db.add(security)

    plan = UserPlan(
        user_id=user.id,
        plan_name="monthly",
        price_in_rupees=MONTHLY_PLAN_PRICE_INR,
        status="active",
        started_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=MONTHLY_PLAN_DAYS),
        payment_status="paid",
    )
    db.add(plan)
    db.commit()
    return user


def build_user_response(user: User, plan: UserPlan | None, security: UserSecurity | None) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        plan_status=plan.status if plan else "inactive",
        plan_expires_at=plan.expires_at if plan else None,
        security_locked=bool(security and security.security_locked_until and security.security_locked_until > datetime.now(timezone.utc)),
    )


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.app_name, "plan_price_inr": MONTHLY_PLAN_PRICE_INR, "plan_validity_days": MONTHLY_PLAN_DAYS}


@app.post("/api/auth/google/login", response_model=LoginResponse)
async def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    user = get_or_create_demo_user(db)
    security = db.query(UserSecurity).filter(UserSecurity.user_id == user.id).first()
    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()

    if security and security.is_2fa_enabled:
        return LoginResponse(
            success=True,
            message="2FA required for secure login",
            requires_2fa=True,
            user=build_user_response(user, plan, security),
        )

    if not plan or not is_plan_active(plan.expires_at):
        raise HTTPException(status_code=403, detail="Monthly access expired or inactive")

    token = create_cookie_value()
    refresh = generate_refresh_token()
    expiry = datetime.now(timezone.utc) + timedelta(minutes=settings.session_lifetime_minutes)
    refresh_expiry = datetime.now(timezone.utc) + timedelta(days=settings.refresh_lifetime_days)

    db.add(
        UserSession(
            user_id=user.id,
            session_token_hash=hash_value(token),
            refresh_token_hash=hash_value(refresh),
            ip_address="127.0.0.1",
            user_agent="fastapi-test-agent",
            expires_at=expiry,
            refresh_expires_at=refresh_expiry,
            last_activity_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    response = JSONResponse(
        content=LoginResponse(
            success=True,
            message="Login successful",
            user=build_user_response(user, plan, security),
        ).model_dump()
    )
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.session_lifetime_minutes * 60,
    )
    return response


@app.post("/api/auth/2fa/verify", response_model=LoginResponse)
async def verify_two_fa(payload: Verify2FARequest, db: Session = Depends(get_db)):
    user = get_or_create_demo_user(db)
    security = db.query(UserSecurity).filter(UserSecurity.user_id == user.id).first()
    if not security or not security.is_2fa_enabled or not security.secret_key_encrypted:
        raise HTTPException(status_code=400, detail="2FA is not enabled")

    if not verify_totp(security.secret_key_encrypted, payload.code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")

    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
    if not plan or not is_plan_active(plan.expires_at):
        raise HTTPException(status_code=403, detail="Monthly access expired or inactive")

    return LoginResponse(
        success=True,
        message="2FA verified and access granted",
        requires_2fa=False,
        user=build_user_response(user, plan, security),
    )


@app.post("/api/billing/activate-monthly")
async def activate_monthly(payload: ActivationRequest, db: Session = Depends(get_db)):
    if payload.amount != MONTHLY_PLAN_PRICE_INR:
        raise HTTPException(status_code=400, detail=f"Incorrect amount. Expected {MONTHLY_PLAN_PRICE_INR} INR")

    user = get_or_create_demo_user(db)
    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
    if not plan:
        plan = UserPlan(user_id=user.id)
        db.add(plan)

    now = datetime.now(timezone.utc)
    plan.plan_name = "monthly"
    plan.price_in_rupees = MONTHLY_PLAN_PRICE_INR
    plan.status = "active"
    plan.started_at = now
    plan.expires_at = now + timedelta(days=MONTHLY_PLAN_DAYS)
    plan.auto_renew = False
    plan.last_payment_id = payload.payment_reference
    plan.payment_status = "paid"
    db.commit()

    return {
        "success": True,
        "plan_status": "active",
        "expires_at": plan.expires_at.isoformat(),
        "price_in_rupees": MONTHLY_PLAN_PRICE_INR,
        "validity_days": MONTHLY_PLAN_DAYS,
        "currency": "INR",
    }


@app.get("/api/billing/status")
async def billing_status(db: Session = Depends(get_db)):
    user = get_or_create_demo_user(db)
    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
    if not plan:
        return {"status": "inactive", "expires_at": None, "remaining_days": 0, "price_in_rupees": MONTHLY_PLAN_PRICE_INR, "currency": "INR"}

    remaining_days = max(0, (plan.expires_at - datetime.now(timezone.utc)).days)
    return {
        "status": plan.status,
        "expires_at": plan.expires_at.isoformat() if plan.expires_at else None,
        "remaining_days": remaining_days,
        "price_in_rupees": plan.price_in_rupees,
        "currency": "INR",
        "validity_days": MONTHLY_PLAN_DAYS,
    }


@app.get("/api/billing/plan-summary")
async def plan_summary():
    return {
        "plan_name": "monthly",
        "price_in_rupees": MONTHLY_PLAN_PRICE_INR,
        "currency": "INR",
        "validity_days": MONTHLY_PLAN_DAYS,
        "renewal_required_after_expiry": True,
        "description": "One month token validity. After expiry, users can log in again and generate a fresh access month.",
    }


@app.get("/api/security/status")
async def security_status(db: Session = Depends(get_db)):
    user = get_or_create_demo_user(db)
    security = db.query(UserSecurity).filter(UserSecurity.user_id == user.id).first()
    return {
        "two_fa_enabled": bool(security and security.is_2fa_enabled),
        "passkey_enabled": bool(security and security.passkey_enabled),
        "security_locked": bool(security and security.security_locked_until and security.security_locked_until > datetime.now(timezone.utc)),
        "suspicious_activity_count": security.suspicious_activity_count if security else 0,
        "monthly_plan_price_inr": MONTHLY_PLAN_PRICE_INR,
        "validity_days": MONTHLY_PLAN_DAYS,
        "alert_channels": ["email", "whatsapp"],
    }


@app.post("/api/security/breach-alert")
async def breach_alert(db: Session = Depends(get_db)):
    user = get_or_create_demo_user(db)
    security = db.query(UserSecurity).filter(UserSecurity.user_id == user.id).first()
    if security:
        security.suspicious_activity_count = (security.suspicious_activity_count or 0) + 1
        security.security_locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
    db.commit()
    return {
        "status": "alert_sent",
        "channels": ["email", "whatsapp"],
        "user": user.email,
        "message": "Security breach alert queued. User must re-verify identity.",
    }


@app.get("/api/auth/me")
async def get_me(db: Session = Depends(get_db)):
    user = get_or_create_demo_user(db)
    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
    security = db.query(UserSecurity).filter(UserSecurity.user_id == user.id).first()
    return build_user_response(user, plan, security).model_dump()


from fastapi.staticfiles import StaticFiles
import os

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists(os.path.join(root_dir, "index.html")):
    app.mount("/", StaticFiles(directory=root_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)

