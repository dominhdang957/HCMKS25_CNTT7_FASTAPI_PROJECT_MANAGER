from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.user import OwnerResponse

class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="Tên dự án")
    description: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Tên dự án không được để trống hoặc chỉ chứa khoảng trắng")
        return v.strip()


class ProjectCreate(ProjectBase):
    pass  # owner_id sẽ lấy từ user đang đăng nhập (current_user), không cần client gửi lên


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Tên dự án không được để trống hoặc chỉ chứa khoảng trắng")
        return v.strip() if v else v


class ProjectResponse(ProjectBase):
    id: int
    owner: OwnerResponse
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)