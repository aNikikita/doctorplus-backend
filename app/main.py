"""
Doctor+ Backend - Production FastAPI Application
Version: 2026-01-02-render-a

Production-ready features:
- Versioned API (/v1/*)
- Client authentication (X-API-Key / Bearer)
- Rate limiting (per IP)
- Standardized error responses
- Safety filtering
- CORS configuration
- Structured logging
"""

import os
import asyncio
import logging
import uuid
import time
import re
from typing import Optional, Literal, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Request, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from groq import AsyncGroq

# Import app modules
from .config import Config
from .security import verify_api_key, get_client_ip
from .rate_limit import check_rate_limit
from .errors import (
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
    create_error_response
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("doctorplus")

# Groq client singleton
_groq_client = None


def get_groq_client() -> AsyncGroq:
    """Get or initialize Groq client with normalized API key."""
    global _groq_client
    if _groq_client is None:
        if not Config.GROQ_API_KEY:
            logger.error("GROQ_API_KEY not configured")
            raise ValueError("GROQ_API_KEY not set")
        
        logger.info(f"Initializing Groq client (key length: {len(Config.GROQ_API_KEY)})")
        _groq_client = AsyncGroq(api_key=Config.GROQ_API_KEY)
    
    return _groq_client


# Pydantic models
class DoctorPlusRequest(BaseModel):
    """Request model for /doctorplus endpoint."""
    mode: Literal["symptoms", "analyses"] = Field(
        ..., description="Analysis mode: symptoms or lab analyses"
    )
    text: str = Field(..., min_length=1, description="User input text")
    image_b64: Optional[str] = Field(None, description="Optional base64 image")


class DoctorPlusResponse(BaseModel):
    """Response model for /doctorplus endpoint."""
    answer_md: str = Field(..., description="AI response in Markdown")
    usage: Optional[dict] = Field(None, description="Token usage stats")
    build: str = Field(..., description="Build version")


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"🚀 Doctor+ Backend starting - Build: {Config.BUILD}")
    logger.info(f"   Environment: {Config.ENVIRONMENT.value}")
    logger.info(f"   GROQ_API_KEY: {'✓' if Config.GROQ_API_KEY else '✗'}")
    logger.info(f"   DOCTORPLUS_API_KEY: {'✓' if Config.DOCTORPLUS_API_KEY else '✗'}")
    logger.info(f"   CORS origins: {Config.get_cors_origins()}")
    logger.info(f"   Rate limit: {Config.DOCTORPLUS_RPM} req/min")
    
    yield
    
    # Shutdown
    logger.info("👋 Doctor+ Backend shutting down")


# Initialize FastAPI
app = FastAPI(
    title="Doctor+ Backend API",
    description="Medical AI assistant powered by Groq (50+ audience optimized)",
    version=Config.BUILD,
    lifespan=lifespan
)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# CORS middleware
cors_origins = Config.get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests with timing and request ID"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    client_ip = get_client_ip(request)
    
    # Log request
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} "
        f"from {client_ip}"
    )
    
    try:
        response = await call_next(request)
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Log response
        logger.info(
            f"[{request_id}] {response.status_code} "
            f"latency={latency_ms}ms"
        )
        
        return response
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        logger.error(
            f"[{request_id}] ERROR latency={latency_ms}ms: {str(e)}"
        )
        raise


# Root endpoint
@app.get("/")
async def root():
    """API root - service information and available endpoints"""
    return {
        "service": "doctorplus-backend",
        "build": Config.BUILD,
        "status": "operational",
        "environment": Config.ENVIRONMENT.value,
        "docs_url": "/docs",
        "endpoints": {
            "root": "GET /",
            "health": "GET /health",
            "version": "GET /version",
            "legacy_doctorplus": "POST /doctorplus (deprecated)",
            "v1_root": "GET /v1",
            "v1_health": "GET /v1/health",
            "v1_version": "GET /v1/version",
            "v1_doctorplus": "POST /v1/doctorplus (requires auth)"
        }
    }


# Legacy endpoints (maintained for backward compatibility)
@app.get("/health")
async def health_legacy():
    """Legacy health check endpoint"""
    return {"status": "ok", "build": Config.BUILD}


@app.get("/version")
async def version_legacy():
    """Legacy version information endpoint"""
    return {"service": "doctorplus-backend", "build": Config.BUILD}


# Safety filtering
def check_safety(text: str) -> bool:
    """
    Check if request contains unsafe content.
    Returns True if content is safe, False if unsafe.
    """
    unsafe_patterns = [
        r'\b(суицид|самоубийство|покончить с собой)\b',
        r'\b(убить|убийство|причинить вред)\b',
        r'\b(оружие|бомба|взрыв)\b',
        r'\b(наркотик|героин|кокаин)\b',
    ]
    
    text_lower = text.lower()
    for pattern in unsafe_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return False
    
    return True


def get_safety_response() -> str:
    """Get response for unsafe requests"""
    return """Я вижу, что вам может быть трудно прямо сейчас.

🆘 **Если вам нужна срочная помощь:**

• **Экстренная психологическая помощь**: 051 (круглосуточно, бесплатно)
• **Скорая помощь**: 112 или 103
• **Телефон доверия**: 8-800-2000-122 (бесплатно, анонимно)

Пожалуйста, обратитесь к специалистам — они готовы помочь вам."""


# Doctor+ system prompt for 50+ audience
def get_doctor_plus_prompt() -> str:
    """Get medical safety prompt optimized for 50+ audience"""
    return """Ты — Доктор+, медицинский информационный помощник для людей 50+.

**СТРОГИЕ ПРАВИЛА:**
• Ты НЕ ставишь диагнозы и НЕ назначаешь лечение
• Ты НЕ выписываешь рецепты и НЕ указываешь дозировки
• Ты помогаешь понимать симптомы простым языком
• Ты ВСЕГДА рекомендуешь обратиться к врачу

**ФОРМАТ ОТВЕТА (обязательная структура):**

**1. Что это может быть** (1-3 возможные причины, простым языком)

**2. Что можно сделать сейчас** (безопасные рекомендации: покой, вода, проветривание)

**3. 🚨 Когда нужно срочно к врачу:**
(Красные флаги - перечисли условия, когда нужно немедленно вызывать скорую)

**4. Какие вопросы задать врачу**
(Список конкретных вопросов для уточнения у специалиста)

**5. ⚠️ Важно помнить:**
Я — информационный помощник, не врач. Для точного диагноза и лечения обратитесь к специалисту.

**СТИЛЬ:**
• Простой язык без медицинских терминов
• Короткие предложения
• Крупные буллеты (•)
• Эмодзи для выделения важного
• Поддерживающий тон"""


# Core AI function
async def process_doctorplus_request(
    request: DoctorPlusRequest,
    request_id: str
) -> DoctorPlusResponse:
    """
    Process Doctor+ AI request with safety checks and Groq integration.
    """
    # Safety check
    if not check_safety(request.text):
        logger.warning(f"[{request_id}] Unsafe content detected")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request contains unsafe content"
        )
    
    # Log request details
    text_preview = request.text[:80] if Config.LOG_USER_SNIPPET else ""
    logger.info(
        f"[{request_id}] Processing: mode={request.mode}, "
        f"text_len={len(request.text)}, has_image={bool(request.image_b64)}"
        + (f", preview='{text_preview}...'" if text_preview else "")
    )
    
    # Get Groq client
    try:
        client = get_groq_client()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service not configured"
        )
    
    # Build messages
    system_prompt = get_doctor_plus_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request.text}
    ]
    
    # Call Groq API with timeout
    try:
        logger.info(f"[{request_id}] Calling Groq API: model=llama-3.1-405b-reasoning")
        
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="llama-3.1-405b-reasoning",
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
            ),
            timeout=60.0
        )
        
        content = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        logger.info(
            f"[{request_id}] Groq success: "
            f"model=llama-3.1-405b-reasoning, tokens={usage['total_tokens']}"
        )
        
        return DoctorPlusResponse(
            answer_md=content,
            usage=usage,
            build=Config.BUILD
        )
        
    except asyncio.TimeoutError:
        logger.error(f"[{request_id}] Groq API timeout (>60s)")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI service timeout"
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{request_id}] Groq API error: {error_msg}")
        
        # Handle specific errors
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI service authentication failed"
            )
        
        if "rate" in error_msg.lower() and "limit" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI service rate limit exceeded"
            )
        
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service error: {error_msg}"
        )


# Legacy /doctorplus endpoint (backward compatibility)
@app.post("/doctorplus", response_model=DoctorPlusResponse)
async def doctorplus_legacy(
    request_body: DoctorPlusRequest,
    req: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Legacy Doctor+ AI endpoint (DEPRECATED - use /v1/doctorplus).
    Proxies to new implementation for compatibility.
    """
    request_id = req.state.request_id
    logger.warning(f"[{request_id}] Legacy endpoint /doctorplus used (deprecated)")
    
    response = await process_doctorplus_request(request_body, request_id)
    
    # Add deprecation headers
    return JSONResponse(
        status_code=200,
        content=response.dict(),
        headers={
            "Deprecation": "true",
            "Link": "</v1/doctorplus>; rel=\"successor-version\""
        }
    )


# V1 API Router
v1_router = APIRouter(prefix="/v1", tags=["v1"])


@v1_router.get("")
async def v1_root():
    """V1 API root - list of available endpoints"""
    return {
        "api_version": "v1",
        "build": Config.BUILD,
        "endpoints": {
            "health": "GET /v1/health",
            "version": "GET /v1/version",
            "doctorplus": "POST /v1/doctorplus (requires X-API-Key or Bearer token)"
        },
        "authentication": {
            "method": "API Key",
            "headers": ["X-API-Key", "Authorization: Bearer <token>"]
        }
    }


@v1_router.get("/health")
async def v1_health():
    """V1 health check endpoint"""
    return {
        "status": "ok",
        "build": Config.BUILD,
        "api_version": "v1"
    }


@v1_router.get("/version")
async def v1_version():
    """V1 version information endpoint"""
    return {
        "service": "doctorplus-backend",
        "build": Config.BUILD,
        "api_version": "v1",
        "environment": Config.ENVIRONMENT.value
    }


@v1_router.post("/doctorplus", response_model=DoctorPlusResponse)
async def v1_doctorplus(
    request_body: DoctorPlusRequest,
    req: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    V1 Doctor+ AI endpoint (PRODUCTION).
    Requires authentication via X-API-Key or Authorization: Bearer header.
    """
    request_id = req.state.request_id
    client_ip = get_client_ip(req)
    
    # Check rate limit
    allowed, remaining, reset_time = check_rate_limit(client_ip)
    
    if not allowed:
        logger.warning(
            f"[{request_id}] Rate limit exceeded for {client_ip}: "
            f"{Config.DOCTORPLUS_RPM} req/min"
        )
        return create_error_response(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=f"Rate limit exceeded: {Config.DOCTORPLUS_RPM} requests per minute",
            code="RATE_LIMIT",
            details={
                "limit": Config.DOCTORPLUS_RPM,
                "remaining": 0,
                "reset_at": reset_time
            }
        )
    
    # Process request
    response = await process_doctorplus_request(request_body, request_id)
    
    # Add rate limit headers
    return JSONResponse(
        status_code=200,
        content=response.dict(),
        headers={
            "X-RateLimit-Limit": str(Config.DOCTORPLUS_RPM),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time)
        }
    )


# Mount V1 router
app.include_router(v1_router)


# Debug endpoint (only if enabled)
if Config.DEBUG_ENDPOINTS:
    @app.get("/debug/env")
    async def debug_env():
        """Debug endpoint - show environment configuration (sanitized)"""
        return {
            "build": Config.BUILD,
            "environment": Config.ENVIRONMENT.value,
            "groq": {
                "api_key_set": bool(Config.GROQ_API_KEY),
                "api_key_length": len(Config.GROQ_API_KEY) if Config.GROQ_API_KEY else 0,
                "api_key_last4": Config.GROQ_API_KEY[-4:] if Config.GROQ_API_KEY else None
            },
            "auth": {
                "doctorplus_api_key_set": bool(Config.DOCTORPLUS_API_KEY),
                "require_legacy_auth": Config.REQUIRE_LEGACY_AUTH
            },
            "cors": {
                "allowed_origins": Config.get_cors_origins()
            },
            "rate_limit": {
                "requests_per_minute": Config.DOCTORPLUS_RPM
            },
            "logging": {
                "level": Config.LOG_LEVEL,
                "log_user_snippet": Config.LOG_USER_SNIPPET
            }
        }
