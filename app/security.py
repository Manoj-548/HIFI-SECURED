import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import pyotp

from app.config import settings


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def generate_session_secret() -> str:
    return secrets.token_urlsafe(32)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def verify_totp(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code.strip(), valid_window=1)
    except Exception:
        return False


def is_plan_active(expires_at: Optional[datetime]) -> bool:
    if not expires_at:
        return False
    return expires_at > datetime.now(timezone.utc)


def create_cookie_value() -> str:
    return secrets.token_urlsafe(32)


def sign_payload(payload: dict) -> str:
    import json

    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    key = settings.jwt_secret.encode()
    return hmac.new(key, body, hashlib.sha256).hexdigest()
