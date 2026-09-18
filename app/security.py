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


import base64
import string

def get_fernet():
    try:
        from cryptography.fernet import Fernet
        key = base64.urlsafe_b64encode(hashlib.sha256(settings.jwt_secret.encode()).digest())
        return Fernet(key)
    except Exception:
        return None

def encrypt_credential(plain_text: str) -> str:
    if not plain_text:
        return ""
    fernet = get_fernet()
    if fernet:
        return fernet.encrypt(plain_text.encode()).decode()
    # Fallback encoding with secret XOR key
    key_bytes = hashlib.sha256(settings.jwt_secret.encode()).digest()
    text_bytes = plain_text.encode()
    cipher = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(text_bytes)])
    return "XOR:" + base64.b64encode(cipher).decode()

def decrypt_credential(cipher_text: str) -> str:
    if not cipher_text:
        return ""
    if cipher_text.startswith("XOR:"):
        key_bytes = hashlib.sha256(settings.jwt_secret.encode()).digest()
        raw = base64.b64decode(cipher_text[4:])
        plain = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(raw)])
        return plain.decode(errors="replace")
    fernet = get_fernet()
    if fernet:
        try:
            return fernet.decrypt(cipher_text.encode()).decode()
        except Exception:
            return cipher_text
    return cipher_text

def calculate_password_score(password: str) -> int:
    if not password:
        return 0
    score = 0
    length = len(password)
    if length >= 8:
        score += 20
    if length >= 12:
        score += 25
    if length >= 16:
        score += 15
    if any(c.islower() for c in password):
        score += 10
    if any(c.isupper() for c in password):
        score += 10
    if any(c.isdigit() for c in password):
        score += 10
    if any(c in string.punctuation for c in password):
        score += 10
    return min(score, 100)

def generate_secure_password(length: int = 16, use_uppercase: bool = True, use_digits: bool = True, use_symbols: bool = True) -> str:
    chars = string.ascii_lowercase
    if use_uppercase:
        chars += string.ascii_uppercase
    if use_digits:
        chars += string.digits
    if use_symbols:
        chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    password = []
    password.append(secrets.choice(string.ascii_lowercase))
    if use_uppercase:
        password.append(secrets.choice(string.ascii_uppercase))
    if use_digits:
        password.append(secrets.choice(string.digits))
    if use_symbols:
        password.append(secrets.choice("!@#$%^&*()_+-="))
    
    while len(password) < length:
        password.append(secrets.choice(chars))
    
    secrets.SystemRandom().shuffle(password)
    return "".join(password)

