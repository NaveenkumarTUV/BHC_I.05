from __future__ import annotations

from fastapi import HTTPException, Request, Response

from backend.app.services.bhc_config_db import (
    create_user_session,
    delete_user_session,
    get_session_user,
)

AUTH_COOKIE = "bhc_auth_session"
AUTH_MAX_AGE_SECONDS = 8 * 60 * 60


def get_current_user(request: Request) -> dict | None:
    session_token = request.cookies.get(AUTH_COOKIE, "").strip()
    if not session_token:
        return None
    return get_session_user(session_token)


def require_authenticated_user(request: Request) -> dict:
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login is required.")
    return user


def has_admin_access(request: Request) -> bool:
    user = get_current_user(request)
    return bool(user and user.get("is_admin"))


def require_admin_user(request: Request) -> dict:
    user = require_authenticated_user(request)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access is required.")
    return user


def set_auth_cookie(response: Response, email: str) -> None:
    session_token = create_user_session(email)
    response.set_cookie(
        key=AUTH_COOKIE,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=AUTH_MAX_AGE_SECONDS,
        path="/",
    )


def clear_auth_cookie(response: Response, request: Request | None = None) -> None:
    if request is not None:
        session_token = request.cookies.get(AUTH_COOKIE, "").strip()
        if session_token:
            delete_user_session(session_token)
    response.delete_cookie(key=AUTH_COOKIE, path="/", samesite="lax")