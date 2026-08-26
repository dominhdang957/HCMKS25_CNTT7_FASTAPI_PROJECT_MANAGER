from fastapi import APIRouter, Depends, Request,status
from app.dependencies.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse
from app.schemas.response import APIResponse,api_response
from typing import Optional, List
from app.dependencies.dependencies import RoleChecker
from app.db.database import get_db
from app.services import user_service
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users", tags=["Users"])


@router.get( "/me",
    response_model=APIResponse,
    status_code=200,
    summary="Lấy thông tin cá nhân",
    description="Trả về thông tin của user đang đăng nhập, dựa trên token gửi kèm. Không bao giờ trả password_hash.",)
def get_my_profile(request: Request, current_user: User = Depends(get_current_user)):
    return api_response(
        status.HTTP_200_OK,
        "Lấy thông tin thành công",
        UserResponse.model_validate(current_user),
        request
    )

@router.get("",
    response_model=APIResponse,
    status_code=200,
    summary="Danh sách người dùng (Admin)",
    description="Chỉ Admin mới gọi được. Hỗ trợ tìm theo tên/email (search) và lọc theo trạng thái active (is_active).",)
def list_users(
    request: Request,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["ADMIN"])),
):
    users = user_service.get_users(db, search=search, is_active=is_active)
    return api_response(
        status.HTTP_200_OK,
        f"Lấy danh sách thành công {len(users)} kết quả",
        [UserResponse.model_validate(u) for u in users],
        request
    )