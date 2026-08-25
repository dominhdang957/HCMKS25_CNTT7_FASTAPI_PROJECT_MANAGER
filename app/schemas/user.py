from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.user import UserRole


# ---- Base ----
class UserBase(BaseModel):
    email: EmailStr
    full_name: str


# ---- Create (dùng khi đăng ký/tạo user) ----
class UserCreate(UserBase):
    password: str  # nhận password thô, sẽ hash trước khi lưu DB


# ---- Update (dùng khi sửa thông tin, mọi field đều optional) ----
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


# ---- Response (dùng khi trả về cho client, KHÔNG bao giờ trả password) ----
class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OwnerResponse(UserBase):
    pass

    model_config = ConfigDict(from_attributes=True)