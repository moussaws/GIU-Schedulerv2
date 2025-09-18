from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_database
from app.core.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.models.database import User as UserDB
from app.models.schemas import Token, LoginRequest, User, UserCreate, APIResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(login_request: LoginRequest, db: Session = Depends(get_database)):
    """Authenticate user and return access token."""
    user = authenticate_user(db, login_request.username, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def read_current_user(current_user: UserDB = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@router.post("/register", response_model=APIResponse)
async def register(user_create: UserCreate, db: Session = Depends(get_database)):
    """Register a new user (admin only in production)."""
    # Check if user already exists
    existing_user = db.query(UserDB).filter(
        (UserDB.username == user_create.username) |
        (UserDB.email == user_create.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_create.password)
    db_user = UserDB(
        username=user_create.username,
        email=user_create.email,
        password_hash=hashed_password,
        role=user_create.role,
        is_active=user_create.is_active
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return APIResponse(
        success=True,
        message="User registered successfully",
        data={"user_id": db_user.id}
    )