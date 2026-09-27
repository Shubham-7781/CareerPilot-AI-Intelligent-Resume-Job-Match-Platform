from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserOut, Token, TokenRefresh,
    VerifyEmailRequest, ResendVerificationRequest,
    PasswordResetRequest, PasswordResetConfirm,
)
from app.core.config import settings
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, generate_secure_token,
)
from app.services.email_service import send_verification_email, send_password_reset_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    token = generate_secure_token()
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        verification_token=token,
        verification_token_expires=datetime.utcnow() + timedelta(hours=settings.EMAIL_TOKEN_EXPIRE_HOURS),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    background_tasks.add_task(send_verification_email, user.email, token)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    # Note: we don't hard-block login for unverified accounts, since that
    # locks users out entirely if email delivery isn't configured. The
    # frontend shows a "please verify your email" banner instead. Tighten
    # this to a hard block if your product requires it.
    return Token(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=Token)
def refresh(payload: TokenRefresh, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.get(User, data["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return Token(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == payload.token).first()
    if not user or not user.verification_token_expires or user.verification_token_expires < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification link")

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()
    return {"detail": "Email verified successfully"}


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
def resend_verification(payload: ResendVerificationRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    # Always return a generic success message — don't leak whether the email exists.
    if user and not user.is_verified:
        token = generate_secure_token()
        user.verification_token = token
        user.verification_token_expires = datetime.utcnow() + timedelta(hours=settings.EMAIL_TOKEN_EXPIRE_HOURS)
        db.commit()
        background_tasks.add_task(send_verification_email, user.email, token)
    return {"detail": "If that email is registered and unverified, a new link has been sent."}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(payload: PasswordResetRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    # Always return the same response regardless of whether the account exists,
    # so this endpoint can't be used to enumerate registered emails.
    if user:
        token = generate_secure_token()
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        db.commit()
        background_tasks.add_task(send_password_reset_email, user.email, token)
    return {"detail": "If that email is registered, a password reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == payload.token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link")

    user.hashed_password = hash_password(payload.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    return {"detail": "Password reset successfully. You can now log in."}
