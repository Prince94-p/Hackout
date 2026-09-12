from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class UserRegister(BaseModel):
    name: str
    organization: str
    email: str
    password: str

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
