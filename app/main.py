from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Session as UserSession, User, UserPlan, UserSecurity
from app.schemas import ActivationRequest, GoogleLoginRequest, LoginResponse, UserResponse, Verify2FARequest
from app.security import create_cookie_value, generate_refresh_token, generate_totp_secret, hash_value, is_plan_active, verify_totp

app = FastAPI(title="Token Secured", version="1.0.0")


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.app_name}


@app.post("/api/auth/google/login", response_model=LoginResponse)
async def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == "demo@example.com").first()
    if not user:
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

        UserSecurity(
            user_id=user.id,
            is_2fa_enabled=True,
            two_fa_method="totp",
            secret_key_encrypted=hash_value(generate_totp_secret()),
        )
        UserPlan(
            user_id=user.id,
            plan_name="monthly",
            price_in_rupees=settings.monthly_plan_price_inr,
            status="active",
            started_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            payment_status="paid",
        )

        db.commit()

    security = db.query(UserSecurity).filter(UserSecurity.user_id == user.id).first()
    if security and security.is_2fa_enabled:
        return LoginResponse(success=True, message="2FA required", requires_2fa=True)

    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
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
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                name=user.name,
                plan_status=plan.status,
                plan_expires_at=plan.expires_at,
                security_locked=False,
            ),
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
    user = db.query(User).filter(User.email == "demo@example.com").first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    security = db.query(UserSecurity).filter(UserSecurity.user_id == user.id).first()
    if not security or not security.is_2fa_enabled or not security.secret_key_encrypted:
        raise HTTPException(status_code=400, detail="2FA is not enabled")

    secret = security.secret_key_encrypted
    if not verify_totp(secret, payload.code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")

    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
    if not plan or not is_plan_active(plan.expires_at):
        raise HTTPException(status_code=403, detail="Monthly access expired or inactive")

    return LoginResponse(
        success=True,
        message="2FA verified and access granted",
        requires_2fa=False,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            plan_status=plan.status,
            plan_expires_at=plan.expires_at,
            security_locked=False,
        ),
    )


@app.post("/api/billing/activate-monthly")
async def activate_monthly(payload: ActivationRequest, db: Session = Depends(get_db)):
    if payload.amount != settings.monthly_plan_price_inr:
        raise HTTPException(status_code=400, detail="Incorrect amount")

    user = db.query(User).filter(User.email == "demo@example.com").first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
    if not plan:
        plan = UserPlan(user_id=user.id)
        db.add(plan)

    now = datetime.now(timezone.utc)
    plan.plan_name = "monthly"
    plan.price_in_rupees = settings.monthly_plan_price_inr
    plan.status = "active"
    plan.started_at = now
    plan.expires_at = now + timedelta(days=30)
    plan.auto_renew = False
    plan.last_payment_id = payload.payment_reference
    plan.payment_status = "paid"
    db.commit()

    return {
        "success": True,
        "plan_status": "active",
        "expires_at": plan.expires_at.isoformat(),
        "price_in_rupees": settings.monthly_plan_price_inr,
    }


@app.get("/api/billing/status")
async def billing_status(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == "demo@example.com").first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
    if not plan:
        return {"status": "inactive", "expires_at": None, "remaining_days": 0}

    remaining_days = max(0, (plan.expires_at - datetime.now(timezone.utc)).days)
    return {
        "status": plan.status,
        "expires_at": plan.expires_at.isoformat() if plan.expires_at else None,
        "remaining_days": remaining_days,
        "price_in_rupees": plan.price_in_rupees,
    }


@app.get("/api/security/status")
async def security_status(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == "demo@example.com").first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    security = db.query(UserSecurity).filter(UserSecurity.user_id == user.id).first()
    return {
        "two_fa_enabled": bool(security and security.is_2fa_enabled),
        "passkey_enabled": bool(security and security.passkey_enabled),
        "security_locked": bool(security and security.security_locked_until and security.security_locked_until > datetime.now(timezone.utc)),
        "suspicious_activity_count": security.suspicious_activity_count if security else 0,
    }


@app.get("/api/auth/me")
async def get_me(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == "demo@example.com").first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
    security = db.query(UserSecurity).filter(UserSecurity.user_id == user.id).first()

    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "plan_status": plan.status if plan else "inactive",
        "plan_expires_at": plan.expires_at.isoformat() if plan and plan.expires_at else None,
        "security_locked": bool(security and security.security_locked_until and security.security_locked_until > datetime.now(timezone.utc)),
    }
