from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password
from app.core.exceptions import BadRequestException


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