from datetime import datetime, timedelta
from typing import Optional
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


async def get_user_from_token(token: str, db) -> Optional["User"]:
    from app.crud.user import user_crud
    from app.models.user import User

    payload = decode_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    token_type = payload.get("type")

    if user_id is None or token_type != "access":
        return None

    try:
        user = await user_crud.get_by_id(db, uuid.UUID(user_id))
        return user
    except (ValueError, Exception):
        return None
