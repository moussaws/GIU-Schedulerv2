from datetime import datetime, timedelta
from typing import Optional
import hashlib
import hmac
import base64
import json
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import get_database
from app.models.database import User
import os

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using simple SHA256."""
    # Simple hash verification for deployment (not production-ready)
    simple_hash = hashlib.sha256((plain_password + SECRET_KEY).encode()).hexdigest()
    return simple_hash == hashed_password


def get_password_hash(password: str) -> str:
    """Generate password hash using simple SHA256."""
    # Simple hash for deployment (not production-ready)
    return hashlib.sha256((password + SECRET_KEY).encode()).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create simple JWT-like access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire.timestamp()})

    # Simple token creation without JWT library
    payload = base64.b64encode(json.dumps(to_encode).encode()).decode()
    signature = hmac.new(
        SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{payload}.{signature}"


def decode_token(token: str) -> dict:
    """Decode simple JWT-like token."""
    try:
        payload, signature = token.split('.')

        # Verify signature
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid signature")

        # Decode payload
        decoded_payload = json.loads(base64.b64decode(payload.encode()).decode())

        # Check expiration
        if datetime.utcnow().timestamp() > decoded_payload.get("exp", 0):
            raise ValueError("Token expired")

        return decoded_payload
    except Exception:
        raise ValueError("Invalid token")


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current user if they are admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user