"""
Standardized error handling for Doctor+ Backend
All errors return consistent JSON format with error codes
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Optional, Any, Dict

from .config import Config


class ErrorDetail(BaseModel):
    """Standardized error response format"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    build: str


class ErrorResponse(BaseModel):
    """Wrapper for error detail"""
    error: ErrorDetail


# Error code mappings
ERROR_CODES = {
    401: "UNAUTHORIZED",
    404: "NOT_FOUND",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT",
    500: "INTERNAL_ERROR",
    502: "UPSTREAM_ERROR",
    504: "TIMEOUT",
}


def create_error_response(
    status_code: int,
    message: str,
    code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create standardized error response.
    
    Args:
        status_code: HTTP status code
        message: Human-readable error message
        code: Error code (auto-generated from status if not provided)
        details: Additional error details
    """
    if code is None:
        code = ERROR_CODES.get(status_code, "ERROR")
    
    error_detail = ErrorDetail(
        code=code,
        message=message,
        details=details,
        build=Config.BUILD
    )
    
    return JSONResponse(
        status_code=status_code,
        content={"error": error_detail.dict(exclude_none=True)}
    )


# Exception handlers

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors (422)"""
    errors = exc.errors()
    
    # Format validation errors
    field_errors = {}
    for error in errors:
        field = ".".join(str(loc) for loc in error["loc"])
        field_errors[field] = error["msg"]
    
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Request validation failed",
        code="VALIDATION_ERROR",
        details={"fields": field_errors}
    )


async def http_exception_handler(request: Request, exc: Exception):
    """Handle HTTPException with standardized format"""
    from fastapi import HTTPException
    
    if not isinstance(exc, HTTPException):
        # Generic exception
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error",
            code="INTERNAL_ERROR"
        )
    
    # Map known error messages to codes
    detail = str(exc.detail)
    code = None
    
    # AI-specific errors
    if "AI service not configured" in detail or "not configured" in detail:
        code = "AI_NOT_CONFIGURED"
    elif "AI service timeout" in detail or "timeout" in detail.lower():
        code = "AI_TIMEOUT"
    elif "rate limit" in detail.lower():
        code = "AI_RATE_LIMIT" if exc.status_code == 429 else "RATE_LIMIT"
    elif "authentication failed" in detail.lower():
        code = "AI_AUTH_FAILED"
    elif "AI service error" in detail or "upstream" in detail.lower():
        code = "AI_UPSTREAM_ERROR"
    elif "Invalid or missing API key" in detail:
        code = "UNAUTHORIZED"
    elif "unsafe" in detail.lower():
        code = "UNSAFE_REQUEST"
    
    return create_error_response(
        status_code=exc.status_code,
        message=detail,
        code=code
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    import logging
    logger = logging.getLogger("doctorplus")
    logger.exception(f"Unhandled exception: {exc}")
    
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred",
        code="INTERNAL_ERROR"
    )
