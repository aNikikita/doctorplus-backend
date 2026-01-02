"""
Security middleware and authentication for Doctor+ Backend
"""

from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPBearer
from typing import Optional

from .config import Config


# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def verify_api_key(request: Request) -> bool:
    """
    Verify API key from X-API-Key or Authorization header.
    Returns True if authentication is successful.
    Raises HTTPException(401) if authentication is required but fails.
    """
    # Check if auth is required for this path
    if not Config.is_auth_required(request.url.path):
        return True
    
    # No API key configured - allow in dev, deny in prod
    if not Config.DOCTORPLUS_API_KEY:
        if Config.ENVIRONMENT.value == "dev":
            return True
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API authentication not configured"
        )
    
    # Try X-API-Key header
    api_key = request.headers.get("X-API-Key", "").strip()
    
    # Try Authorization: Bearer header
    if not api_key:
        auth_header = request.headers.get("Authorization", "").strip()
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:].strip()
    
    # Verify key
    if api_key and api_key == Config.DOCTORPLUS_API_KEY:
        return True
    
    # Authentication failed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "Bearer"}
    )


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, considering X-Forwarded-For"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take first IP from X-Forwarded-For chain
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
