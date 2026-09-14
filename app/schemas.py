from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class GoogleLoginRequest(BaseModel):
    code: str
    redirect_uri: Optional[str] = None


class Verify2FARequest(BaseModel):
    code: str
    device_id: Optional[str] = None


class ActivationRequest(BaseModel):
    payment_reference: str
    amount: int
    currency: str = "INR"


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    plan_status: str
    plan_expires_at: Optional[datetime] = None
    security_locked: bool = False


class LoginResponse(BaseModel):
    success: bool
    message: str
    requires_2fa: bool = False
    user: Optional[UserResponse] = None
