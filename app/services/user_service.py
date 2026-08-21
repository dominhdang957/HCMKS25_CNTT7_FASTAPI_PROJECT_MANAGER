from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password,verify_password
from app.core.exceptions import BadRequestException,UnauthorizedException,ForbiddenException
from typing import Optional
from sqlalchemy import or_


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    # Kiểm tra email đã tồn tại chưa
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise BadRequestException(detail="Email đã được sử dụng")

    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user:
        raise UnauthorizedException(detail="Email hoặc mật khẩu không đúng")
    if not verify_password(password, user.password_hash):
        raise UnauthorizedException(detail="Email hoặc mật khẩu không đúng")
    if not user.is_active:
        raise ForbiddenException(detail="Tài khoản đã bị khóa")
    return user

def get_users(
    db: Session,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> list[User]:
    query = db.query(User)

    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    return query.order_by(User.created_at.desc()).all()