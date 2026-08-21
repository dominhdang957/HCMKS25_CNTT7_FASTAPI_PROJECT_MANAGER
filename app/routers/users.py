from fastapi import APIRouter, Depends, Request,status
from app.dependencies.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse
from app.schemas.response import APIResponse,api_response
from typing import Optional, List
from app.dependencies.dependencies import require_admin
from app.db.database import get_db
from app.services import user_service
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=APIResponse)
def get_my_profile(request: Request, current_user: User = Depends(get_current_user)):
    return api_response(
        status.HTTP_200_OK,
        "Lấy thông tin thành công",
        UserResponse.model_validate(current_user),
        request
    )

