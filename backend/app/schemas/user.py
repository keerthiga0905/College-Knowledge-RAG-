from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserLogin(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")

class AdminLogin(BaseModel):
    email: EmailStr = Field(..., description="Admin email address")
    password: str = Field(..., min_length=1, description="Admin password")

class UserResponse(BaseModel):
    user_id: str
    name: str
    email: str
    role: str = "student"  # "student" or "admin"
    created_at: datetime

    class Config:
        from_attributes = True
