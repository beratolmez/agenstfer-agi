from __future__ import annotations

import hmac
from typing import Annotated

from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agi_server.config import Settings, get_settings
from agi_server.db import AuditEvent, User, get_db

password_hasher = PasswordHasher()


class BootstrapRequest(BaseModel):
    token: str
    email: EmailStr
    name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=12, max_length=256)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserView(BaseModel):
    id: str
    email: str
    name: str
    roles: list[str]

    @classmethod
    def from_row(cls, user: User) -> UserView:
        return cls(id=user.id, email=user.email, name=user.name, roles=user.roles)


def bootstrap_admin(payload: BootstrapRequest, db: Session, settings: Settings) -> User:
    if db.scalar(select(func.count()).select_from(User)):
        raise HTTPException(status_code=409, detail="İlk admin daha önce oluşturulmuş")
    if not hmac.compare_digest(payload.token, settings.bootstrap_token):
        raise HTTPException(status_code=403, detail="Bootstrap token geçersiz")
    user = User(
        email=str(payload.email).lower(),
        name=payload.name,
        password_hash=password_hasher.hash(payload.password),
        roles=["admin", "analyst", "approver"],
    )
    db.add(user)
    db.flush()
    db.add(
        AuditEvent(actor_id=user.id, action="auth.bootstrap", target_type="user", target_id=user.id)
    )
    db.commit()
    return user


def authenticate(payload: LoginRequest, db: Session) -> User:
    user = db.scalar(
        select(User).where(User.email == str(payload.email).lower(), User.active.is_(True))
    )
    if not user:
        raise HTTPException(status_code=401, detail="E-posta veya parola hatalı")
    try:
        password_hasher.verify(user.password_hash, payload.password)
    except Exception as error:
        raise HTTPException(status_code=401, detail="E-posta veya parola hatalı") from error
    return user


def current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User | None:
    user_id = request.session.get("user_id")
    if user_id:
        return db.get(User, user_id)
    if settings.demo_no_auth:
        return None
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Oturum gerekli")


def require_role(role: str):
    def dependency(
        user: Annotated[User | None, Depends(current_user)],
        settings: Annotated[Settings, Depends(get_settings)],
    ) -> User | None:
        if settings.demo_no_auth and user is None:
            return None
        if not user or role not in user.roles:
            raise HTTPException(status_code=403, detail=f"'{role}' rolü gerekli")
        return user

    return dependency
