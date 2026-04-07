from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.user import UserCreate, UserResponse, UserLogin

from core.database import get_db
from core.dependencies import get_current_active_user
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from models.user import User, PasswordResetToken
from schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserProfile,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# POST /auth/users 
@router.post(
    "/users",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    # Check email uniqueness
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email is already registered")

    # Check username uniqueness
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username is already taken")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# POST /auth/login 
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT tokens",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(user.user_id, user.email),
        refresh_token=create_refresh_token(user.user_id),
        user_id=user.user_id,
        username=user.username,
        full_name=user.full_name,
    )


#  POST /auth/refresh 
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Update/Refresh access token",
)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_data = decode_token(payload.refresh_token)

    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(
        User.user_id == int(token_data["sub"]),
        User.is_active == True,
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return TokenResponse(
        access_token=create_access_token(user.user_id, user.email),
        refresh_token=create_refresh_token(user.user_id),
        user_id=user.user_id,
        username=user.username,
        full_name=user.full_name,
    )


# GET /auth/profile
@router.get(
    "/profile",
    response_model=UserProfile,
    summary="Get current user profile",
)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


# POST /auth/passwords/reset
@router.post(
    "/passwords/reset",
    summary="Request a password reset",
)
def password_reset_request(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if user:
        # Generate hashable token
        reset_token = create_access_token(user.user_id, user.email)
       # Store in the new table you defined 
        reset_entry = PasswordResetToken(
            user_id=user.user_id,
            token_hash=raw_token, # In production, hash this again before storing
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_used=False
        )
        db.add(reset_entry)
        db.commit()
        print(f"[DEV] Password reset token for {user.email}: {reset_token}")

    return {"message": "If that email exists, a reset link has been sent"}


# POST /auth/passwords/reset
@router.put(
    "/passwords/resets",
    summary="Confirm password reset with token and new password",
)
def password_reset_confirm(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    token_data = decode_token(payload.token)

    if not token_data or token_data.get("type") != "access":
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.user_id == int(token_data["sub"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password updated successfully"}


# POST /auth/logout 
@router.post(
    "/logout",
    summary="Logout",
)
def logout(current_user: User = Depends(get_current_active_user)):
    # JWT is stateless- happens on the client side - Add Redis blocklist later.
    return {"message": "Logged out successfully"}