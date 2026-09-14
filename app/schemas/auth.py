from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re

class UserRegister(BaseModel):
    name: str = Field(..., min_length=1)
    organization: str = Field(..., min_length=1)
    email: str
    password: str = Field(..., min_length=8)

    @field_validator("password")
    def password_bytes(cls, v):
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return v

    @field_validator('name', 'organization')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator('email')
    def validate_email(cls, v):
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", v.strip()):
            raise ValueError("Invalid email format")
        return v.lower().strip()

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    organization: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    has_factory: bool
    factory_id: Optional[int] = None
