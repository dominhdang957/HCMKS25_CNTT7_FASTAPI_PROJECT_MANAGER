from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.core.exceptions import UnauthorizedException, ForbiddenException
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:

    if credentials is None:
        raise UnauthorizedException(detail="Thiếu token xác thực")
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except ExpiredSignatureError:
        raise UnauthorizedException(detail="Token đã hết hạn, vui lòng đăng nhập lại")
    except InvalidTokenError:
        raise UnauthorizedException(detail="Token không hợp lệ")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException(detail="Token không hợp lệ")

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