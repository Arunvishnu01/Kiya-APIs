from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone_e164: Optional[str] = Field(default=None, max_length=20)
    password: str = Field(min_length=6, max_length=128)
    full_name: str = Field(min_length=1, max_length=150)

    @model_validator(mode="after")
    def check_identifier(self) -> "RegisterRequest":
        if not self.email and not self.phone_e164:
            raise ValueError("Either email or phone_e164 must be provided")
        return self


class LoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone_e164: Optional[str] = Field(default=None, max_length=20)
    password: str = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def check_identifier(self) -> "LoginRequest":
        if not self.email and not self.phone_e164:
            raise ValueError("Either email or phone_e164 must be provided")
        return self


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str = "USER"
    user_id: str
    full_name: str = "User"
    onboarding_completed: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str
