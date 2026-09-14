from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import SecurityEvent, Session as UserSession, User, UserPlan, UserSecurity


async def revoke_user_sessions(db: Session, user_id: UUID) -> None:
    db.query(UserSession).filter(UserSession.user_id == user_id).update({"is_active": False, "revoked_at": datetime.now(timezone.utc)})
    db.commit()


async def trigger_breach_alert(db: Session, user: User, ip_address: str, device_id: str, reason: str) -> None:
    event = SecurityEvent(
        user_id=user.id,
        event_type="suspicious_login",
        severity="high",
        ip_address=ip_address,
        device_id=device_id,
        notes=reason,
    )
    db.add(event)

    security = db.query(UserSecurity).filter(UserSecurity.user_id == user.id).first()
    if security:
        security.suspicious_activity_count = (security.suspicious_activity_count or 0) + 1
        security.security_locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)

    await revoke_user_sessions(db, user.id)
    db.commit()


async def check_plan_validity(db: Session, user_id: UUID) -> bool:
    plan = db.query(UserPlan).filter(UserPlan.user_id == user_id).first()
    if not plan or not plan.expires_at:
        return False
    return plan.expires_at > datetime.now(timezone.utc)
