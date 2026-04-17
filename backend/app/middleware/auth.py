"""FastAPI 认证依赖注入。

提供三种依赖函数：
- get_current_user: 强制认证，从 JWT token 解析当前用户。
- require_admin: 基于 get_current_user，额外校验管理员角色。
- get_current_user_optional: 可选认证，token 有效时返回用户，否则返回 None。
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.models.auth_models import User
from app.models.db import get_db
from app.services.auth import decode_access_token

# OAuth2 token 提取器，默认从 Authorization: Bearer <token> 获取
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """解析 JWT token 并返回当前用户对象。

    从 Authorization header 提取 token，解码后通过 sub 字段查询数据库。
    用户不存在或已禁用时抛出 401 异常。

    返回:
        当前登录的 User 实例。

    异常:
        HTTPException(401): token 无效/过期，或用户不存在/已禁用。
    """
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的认证令牌",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的认证令牌",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的认证令牌",
        )

    return user


def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """校验当前用户是否为管理员。

    基于 get_current_user 获取用户后，检查 role 字段。

    返回:
        当前登录的管理员 User 实例。

    异常:
        HTTPException(403): 当前用户不是管理员。
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user


def get_current_user_optional(
    db: Annotated[Session, Depends(get_db)],
    token: str | None = Depends(OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)),
) -> User | None:
    """可选认证依赖。

    当请求携带有效的 Authorization: Bearer token 时，返回对应 User；
    无 token 或 token 无效时返回 None，不阻断请求。

    适用场景：登录与非登录用户均可访问的端点。

    返回:
        有效 token 对应的 User 实例，或 None。
    """
    if token is None:
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        return None

    return user
