"""JWT 认证与密码加密服务"""

import logging
from datetime import datetime, timedelta

from jose import JWTError, ExpiredSignatureError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models.auth_models import LoginLog, OperationLog, User

logger = logging.getLogger(__name__)

# 密码加密上下文，使用 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """对明文密码进行 bcrypt 加密。

    使用 passlib CryptContext 处理加密；若 passlib 不可用，则回退至原生 bcrypt。
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与哈希值是否匹配。

    返回 True 表示密码正确，False 表示不匹配。
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """创建 JWT 访问令牌。

    参数:
        data: 需要编码到 token 中的载荷数据（通常包含 sub=user_id）。
        expires_delta: 令牌过期时间偏移量；未提供时使用配置的默认值。

    返回:
        编码后的 JWT 字符串。
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(hours=settings.jwt_expire_hours)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    """解码并校验 JWT 访问令牌。

    返回:
        解码后的 payload 字典；若令牌过期或无效则返回 None。
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except ExpiredSignatureError:
        logger.warning("JWT token 已过期")
        return None
    except JWTError:
        logger.warning("JWT token 无效或格式错误")
        return None


def authenticate_user(
    db: Session, username_or_email: str, password: str
) -> User | None:
    """通过用户名或邮箱登录验证。

    参数:
        db: 数据库会话。
        username_or_email: 用户输入的用户名或邮箱。
        password: 明文密码。

    返回:
        验证成功返回 User 对象；失败或用户被禁用时返回 None。
    """
    user = (
        db.query(User)
        .filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        )
        .first()
    )
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def log_login(db: Session, user_id: int, ip_address: str, user_agent: str, status: str) -> None:
    """记录用户登录日志。

    参数:
        db: 数据库会话。
        user_id: 登录用户 ID。
        ip_address: 客户端 IP 地址。
        user_agent: 客户端 User-Agent 信息。
        status: 登录结果状态（success / failed）。
    """
    record = LoginLog(
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
    )
    db.add(record)
    db.commit()


def log_operation(
    db: Session,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: int | None = None,
    detail: str | None = None,
) -> None:
    """记录用户操作日志。

    参数:
        db: 数据库会话。
        user_id: 操作用户 ID。
        action: 操作类型描述（如 create、update、delete）。
        resource_type: 被操作的资源类型（如 resume、user）。
        resource_id: 被操作的资源 ID（可选）。
        detail: 操作详情，可存储 JSON 字符串（可选）。
    """
    record = OperationLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
    )
    db.add(record)
    db.commit()
