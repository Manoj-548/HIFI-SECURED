from datetime import datetime
from uuid import uuid4, UUID as PyUUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[PyUUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    google_user_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(80), nullable=True)

    security = relationship("UserSecurity", back_populates="user", uselist=False)
    plan = relationship("UserPlan", back_populates="user", uselist=False)
    sessions = relationship("Session", back_populates="user")


class UserSecurity(Base):
    __tablename__ = "user_security"

    id: Mapped[PyUUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[PyUUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    two_fa_method: Mapped[str] = mapped_column(String(40), default="totp", nullable=False)
    secret_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    backup_codes_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    passkey_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_security_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    suspicious_activity_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    security_locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    breach_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="security")


class UserPlan(Base):
    __tablename__ = "user_plan"

    id: Mapped[PyUUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[PyUUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    plan_name: Mapped[str] = mapped_column(String(80), default="monthly", nullable=False)
    price_in_rupees: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="inactive", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)

    user = relationship("User", back_populates="plan")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[PyUUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[PyUUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    session_token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    refresh_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="sessions")


class AccessLog(Base):
    __tablename__ = "access_logs"

    id: Mapped[PyUUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[PyUUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    session_id: Mapped[PyUUID | None] = mapped_column(ForeignKey("sessions.id"), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    endpoint: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id: Mapped[PyUUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[PyUUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), default="medium", nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notified_email: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notified_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id: Mapped[PyUUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[PyUUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[PyUUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[PyUUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    trusted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[PyUUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[PyUUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    notification_type: Mapped[str] = mapped_column(String(120), nullable=False)
    channel: Mapped[str] = mapped_column(String(40), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="queued", nullable=False)
    delivery_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)


class VaultItem(Base):
    __tablename__ = "vault_items"

    id: Mapped[PyUUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[PyUUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    account_holder_name: Mapped[str] = mapped_column(String(255), default="Primary Account Holder", nullable=False)
    service_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="General", nullable=False)
    login_email_username: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    security_score: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_shared_with_specific_user: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class InvisibleToken(Base):
    __tablename__ = "invisible_tokens"

    id: Mapped[PyUUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[PyUUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    platform_name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform_icon: Mapped[str] = mapped_column(String(50), default="bi-shield-lock", nullable=False)
    token_label: Mapped[str] = mapped_column(String(255), nullable=False)
    token_secret_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    zero_knowledge_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[str] = mapped_column(Text, default="read:write", nullable=False)
    expiry_minutes: Mapped[int] = mapped_column(Integer, default=1440, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE & ENCRYPTED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BranchToken(Base):
    __tablename__ = "branch_tokens"

    id: Mapped[PyUUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[PyUUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    branch_name: Mapped[str] = mapped_column(String(150), nullable=False)
    commit_sha: Mapped[str] = mapped_column(String(80), nullable=False)
    author_email: Mapped[str] = mapped_column(String(255), nullable=False)
    associated_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rotation_status: Mapped[str] = mapped_column(String(50), default="SYNCED & PROTECTED", nullable=False)
    last_rotated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class BootstrapFailureLog(Base):
    __tablename__ = "bootstrap_failure_logs"

    id: Mapped[PyUUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[PyUUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    failure_type: Mapped[str] = mapped_column(String(100), nullable=False)  # "BIOMETRIC_FAIL", "TOKEN_MISMATCH", "PR_AUTH_FAIL"
    sanitized_error_code: Mapped[str] = mapped_column(String(100), nullable=False) # Zero-leak code e.g. "ERR-BOOTSTRAP-401-OBFUSCATED"
    platform_or_branch: Mapped[str] = mapped_column(String(150), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)




