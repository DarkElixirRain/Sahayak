from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's raw password")
    name: Optional[str] = Field(None, description="User's display name")


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's raw password")


class UserResponse(BaseModel):
    id: str = Field(..., description="User ID (UUID)")
    email: str = Field(..., description="User's email address")
    name: Optional[str] = Field(None, description="User's display name")

    model_config = {
        "from_attributes": True
    }


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
