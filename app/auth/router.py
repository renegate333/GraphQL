"""REST-эндпоинты /auth/*: регистрация, логин, текущий пользователь."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.audit.service import write_event
from app.auth.schemas import Credentials, MeResponse, TokenResponse
from app.core.deps import get_current_user
from app.core.jwt import create_access_token
from app.core.passwords import (
    WeakPasswordError,
    hash_password,
    validate_policy,
    verify_password,
)
from app.db.session import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_info(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua


@router.post("/register", response_model=TokenResponse)
def register(payload: Credentials, request: Request, db: Session = Depends(get_db)):
    # email занят?
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # политика пароля
    try:
        validate_policy(payload.password, user_inputs=[payload.email])
    except WeakPasswordError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # создаём пользователя
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    ip, ua = _client_info(request)
    write_event(
        db,
        event_type="user.created",
        actor_id=user.id,
        ip=ip,
        user_agent=ua,
        metadata={"email": user.email},
    )

    token = create_access_token(sub=user.email)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: Credentials, request: Request, db: Session = Depends(get_db)):
    ip, ua = _client_info(request)
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        write_event(
            db,
            event_type="user.login.failure",
            ip=ip,
            user_agent=ua,
            metadata={"email": payload.email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    write_event(
        db,
        event_type="user.login.success",
        actor_id=user.id,
        ip=ip,
        user_agent=ua,
        metadata={"email": user.email},
    )
    token = create_access_token(sub=user.email)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)):
    return MeResponse(id=user.id, email=user.email, is_admin=user.is_admin)