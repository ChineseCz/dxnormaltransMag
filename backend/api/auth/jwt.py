"""
JWT token issue/verify/revoke helpers.

Environment variables:
- JWT_SECRET: signing key
- JWT_EXPIRE: access token TTL in seconds (default 86400)
- JWT_REFRESH_EXPIRE: refresh token TTL in seconds
- REDIS_URL: optional redis backend for revoke list
"""
from __future__ import annotations

import os
import time
import uuid
import threading
from typing import Optional, Dict, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.environ.get("JWT_SECRET") or os.environ.get("JWT_SECRET_KEY") or "change_me_in_production_please"
ALGORITHM = "HS256"
EXPIRE_SECS = int(os.environ.get("JWT_EXPIRE", "86400"))
REFRESH_SECS = int(os.environ.get("JWT_REFRESH_EXPIRE", str(EXPIRE_SECS * 7)))

if ALGORITHM.startswith("HS") and len(SECRET_KEY.encode("utf-8")) < 32:
    print("[auth] WARNING: JWT_SECRET length is below 32 bytes; rotate to a stronger key.")

_mem_blacklist: Dict[str, float] = {}
_mem_lock = threading.Lock()

_redis_client: Optional[Any] = None
try:
    import redis as _redis_mod

    _r = _redis_mod.from_url(
        os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
        socket_connect_timeout=2,
    )
    _r.ping()
    _redis_client = _r
    print("[auth] revoke backend: Redis")
except Exception:
    print("[auth] revoke backend: in-memory dictionary")


def _mem_cleanup():
    now = time.time()
    with _mem_lock:
        for k in [k for k, v in _mem_blacklist.items() if v < now]:
            del _mem_blacklist[k]


def create_access_token(user_id: int, username: str, role: str) -> tuple[str, str]:
    """Create access token and return (token, jti)."""
    now = int(time.time())
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "jti": jti,
        "iat": now,
        "exp": now + EXPIRE_SECS,
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM), jti


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


def revoke_token(jti: str, expire_at: float) -> None:
    ttl = int(expire_at - time.time()) + 10
    if ttl <= 0:
        return
    if _redis_client:
        _redis_client.setex(f"bl:{jti}", ttl, "1")
    else:
        with _mem_lock:
            _mem_blacklist[jti] = expire_at
        threading.Thread(target=_mem_cleanup, daemon=True).start()


def is_revoked(jti: str) -> bool:
    if _redis_client:
        return bool(_redis_client.exists(f"bl:{jti}"))
    with _mem_lock:
        entry = _mem_blacklist.get(jti)
    if entry is None:
        return False
    if entry < time.time():
        with _mem_lock:
            _mem_blacklist.pop(jti, None)
        return False
    return True


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    """FastAPI dependency: parse Authorization: Bearer <token>."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if is_revoked(payload.get("jti", "")):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token revoked, please login again")
    return payload


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "管理员":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user

