from fastapi import APIRouter, Depends, Request,status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.response import APIResponse
from app.services import user_service
from app.schemas.response import api_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=APIResponse)
def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    new_user = user_service.create_user(db, user_data)
    return api_response(
        status.HTTP_201_CREATED,
        "Đăng ký tài khoản thành công",
        UserResponse.model_validate(new_user),
        request
    )