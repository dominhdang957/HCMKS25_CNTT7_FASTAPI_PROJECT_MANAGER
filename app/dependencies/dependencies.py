from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jwt.exceptions import PyJWTError
from typing import List

from app.db.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.core.exceptions import UnauthorizedException, ForbiddenException

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials

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


def require_role(allowed_roles: List[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(detail="Bạn không có quyền thực hiện thao tác này")
        return current_user
    return role_checker


# Dùng sẵn cho case phổ biến nhất — chỉ Admin
require_admin = require_role([UserRole.ADMIN])