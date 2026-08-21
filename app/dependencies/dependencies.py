# app/core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jwt import PyJWTError

from app.db.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.core.exceptions import UnauthorizedException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException()
    except PyJWTError:
        raise UnauthorizedException(detail="Token không hợp lệ hoặc đã hết hạn")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedException(detail="Không tìm thấy user")
    return user