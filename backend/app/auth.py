"""
Supabase JWT verification.

The frontend signs in against Supabase directly and sends the resulting access
token as `Authorization: Bearer <jwt>`. This module turns that token into a
user id, or rejects it. The backend never sees a password and stores no
credentials of its own.

Two signing schemes are supported, because which one a project uses depends on
when it was created:

  - Asymmetric (ES256/RS256). The current default. Supabase publishes public
    keys at a JWKS endpoint; we fetch and cache them. No shared secret exists,
    so nothing signing-related needs to be configured on this side beyond the
    project URL.
  - Symmetric (HS256). Legacy projects. Verified with the project's JWT secret,
    which must be set as SUPABASE_JWT_SECRET.

Set SUPABASE_JWT_SECRET and you get HS256; leave it unset and you get JWKS.
"""

import logging
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.config import settings

log = logging.getLogger(__name__)

# Supabase stamps every access token with this audience.
AUDIENCE = "authenticated"
ASYMMETRIC_ALGORITHMS = ["ES256", "RS256"]

# auto_error=False so a missing header produces our own 401 with a useful
# message, rather than FastAPI's bare 403.
bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    # Cached because it holds its own key cache - rebuilding it per request
    # would refetch the JWKS every time.
    return PyJWKClient(settings.jwks_url)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def verify_token(token: str) -> str:
    """Verify a Supabase access token and return its user id (the `sub` claim)."""
    try:
        if settings.supabase_jwt_secret:
            claims = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience=AUDIENCE,
            )
        else:
            if not settings.supabase_url:
                # Misconfiguration, not a bad token. Loud, because every
                # request will fail until it's fixed.
                log.error("auth is enabled but SUPABASE_URL is not set")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Auth is misconfigured on the server.",
                )
            signing_key = _jwks_client().get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=ASYMMETRIC_ALGORITHMS,
                audience=AUDIENCE,
                issuer=settings.jwt_issuer,
            )
    except jwt.ExpiredSignatureError as exc:
        raise _unauthorized("Session expired. Sign in again.") from exc
    except jwt.PyJWTError as exc:
        # Covers bad signature, wrong audience/issuer, malformed token. The
        # reason is deliberately not echoed back to the caller.
        log.warning("token rejected", extra={"reason": type(exc).__name__})
        raise _unauthorized("Invalid authentication token.") from exc

    user_id = claims.get("sub")
    if not user_id:
        raise _unauthorized("Token is missing a subject claim.")
    return user_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """FastAPI dependency resolving the caller to a user id."""
    if not settings.auth_enabled:
        return settings.dev_user_id
    if credentials is None:
        raise _unauthorized("Not authenticated.")
    return verify_token(credentials.credentials)
