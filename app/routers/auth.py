from fastapi import APIRouter, Depends, Request,status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.response import APIResponse
from app.services import user_service
from app.schemas.response import api_response
from app.schemas.auth import LoginRequest, TokenResponse
from app.core.security import create_access_token
from app.dependencies.dependencies import get_current_user,require_admin
from app.models.user import User


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

@router.post("/login", response_model=APIResponse)
def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = user_service.authenticate_user(db, login_data.email, login_data.password)

    access_token = create_access_token(data={"sub": str(user.id)})

    return api_response(
        status.HTTP_200_OK,
        "Đăng nhập thành công",
        TokenResponse(access_token=access_token),
        request
    )

@router.get("/me", response_model=APIResponse)
def get_me(request: Request, current_user: User = Depends(get_current_user)):
    return api_response(
        status.HTTP_200_OK,
        "Lấy thông tin thành công",
        UserResponse.model_validate(current_user),
        request
    )

@router.get("/admin-only")
def admin_only_route(current_user: User = Depends(require_admin)):
    return {"message": f"Xin chào Admin {current_user.full_name}"}