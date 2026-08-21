from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jwt.exceptions import PyJWTError

from app.db.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.core.exceptions import UnauthorizedException

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials  # lấy phần token từ "Bearer <token>"

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException(detail="Token không hợp lệ")
    except PyJWTError:
        raise UnauthorizedException(detail="Token không hợp lệ hoặc đã hết hạn")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise UnauthorizedException(detail="Không tìm thấy user")
    if not user.is_active:
        raise UnauthorizedException(detail="Tài khoản đã bị khóa")

    return user