import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.core.config import settings
from app.models.user import User, UserProfile
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
)

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user account and return access + refresh tokens."""

    # Check uniqueness
    if payload.email:
        result = await db.execute(select(User).where(User.email == payload.email.lower()))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )
    if payload.phone_e164:
        result = await db.execute(select(User).where(User.phone_e164 == payload.phone_e164))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number already exists.",
            )

    # Create user
    user = User(
        email=payload.email.lower() if payload.email else None,
        phone_e164=payload.phone_e164,
        password_hash=hash_password(payload.password),
        role="USER",
        status="ACTIVE",
    )
    db.add(user)
    await db.flush()  # Get the user.id

    # Create profile
    profile = UserProfile(
        user_id=user.id,
        full_name=payload.full_name,
        timezone="Asia/Kolkata",
        onboarding_completed_at=None,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(user)

    # Issue tokens
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=user.role,
        user_id=str(user.id),
        full_name=payload.full_name,
        onboarding_completed=False,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email/phone + password."""

    user: User | None = None

    if payload.email:
        result = await db.execute(
            select(User).where(User.email == payload.email.lower(), User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
    elif payload.phone_e164:
        result = await db.execute(
            select(User).where(User.phone_e164 == payload.phone_e164, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please check your email/phone and password.",
        )

    if user.status == "SUSPENDED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended. Please contact support.",
        )

    # Fetch profile for name
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()
    full_name = profile.full_name if profile else "User"
    onboarding_done = profile.onboarding_completed_at is not None if profile else False

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=user.role,
        user_id=str(user.id),
        full_name=full_name,
        onboarding_completed=onboarding_done,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Issue a new access token using a valid refresh token."""
    token_data = verify_token(payload.refresh_token)
    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    user_id = token_data.get("sub")
    try:
        user_uuid = uuid.UUID(user_id) if user_id else None
    except (ValueError, AttributeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

    if not user_uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

    result = await db.execute(
        select(User).where(User.id == user_uuid, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()
    full_name = profile.full_name if profile else "User"
    onboarding_done = profile.onboarding_completed_at is not None if profile else False

    new_access = create_access_token({"sub": str(user.id), "role": user.role})
    new_refresh = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        role=user.role,
        user_id=str(user.id),
        full_name=full_name,
        onboarding_completed=onboarding_done,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """Logout — client should discard tokens. Server-side session revocation is a future enhancement."""
    return
