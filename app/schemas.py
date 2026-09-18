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


class VaultItemCreate(BaseModel):
    account_holder_name: str = "Primary Account Holder"
    service_name: str
    category: str = "General"
    login_email_username: str
    password: str
    website_url: Optional[str] = None
    notes: Optional[str] = None
    is_favorite: bool = False
    is_shared_with_specific_user: bool = True


class VaultItemUpdate(BaseModel):
    account_holder_name: Optional[str] = None
    service_name: Optional[str] = None
    category: Optional[str] = None
    login_email_username: Optional[str] = None
    password: Optional[str] = None
    website_url: Optional[str] = None
    notes: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_shared_with_specific_user: Optional[bool] = None


class VaultItemResponse(BaseModel):
    id: str
    account_holder_name: str
    service_name: str
    category: str
    login_email_username: str
    decrypted_password: str
    website_url: Optional[str] = None
    notes: Optional[str] = None
    security_score: int
    is_favorite: bool
    is_shared_with_specific_user: bool
    created_at: datetime
    updated_at: datetime


class PasswordGenerateRequest(BaseModel):
    length: int = 16
    use_uppercase: bool = True
    use_digits: bool = True
    use_symbols: bool = True


class PasswordGenerateResponse(BaseModel):
    generated_password: str
    security_score: int


class PlatformTokenCreate(BaseModel):
    platform_name: str
    token_label: str
    scopes: Optional[str] = "read:write"
    expiry_minutes: int = 1440


class PlatformTokenResponse(BaseModel):
    id: str
    platform_name: str
    platform_icon: str
    token_label: str
    secret_reveal: str
    zero_knowledge_hash: str
    scopes: str
    expiry_minutes: int
    status: str
    created_at: datetime
    last_used_at: Optional[datetime] = None


class PlatformTokenRevokeResponse(BaseModel):
    success: bool
    message: str
    token_id: str


class BiometricAuthRequest(BaseModel):
    credential_id: Optional[str] = "webauthn-passkey-001"
    biometric_type: str = "touchpad_touchscreen"  # "touchpad_touchscreen", "windows_hello_key", "face_id", "touch_id"
    user_email: str = "demo@example.com"



class BranchTokenRotateRequest(BaseModel):
    branch_name: str
    rotate_recursively_team: bool = True


class PRBiometricApproveRequest(BaseModel):
    pr_id: str
    reviewer_email: str = "demo@example.com"
    auth_method: str = "biometric"  # "biometric" or "2fa_token"
    passcode: Optional[str] = None


class BootstrapFailureLogResponse(BaseModel):
    id: str
    failure_type: str
    sanitized_error_code: str
    platform_or_branch: str
    is_resolved: bool
    created_at: datetime




