"""
Doctor+ Backend - Production FastAPI Application
Optimized for Render deployment with Docker
"""

import os
import asyncio
import logging
from typing import Optional, Literal

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from groq import AsyncGroq

# Build marker for deployment tracking
BUILD = "2026-01-02-render-a"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("doctorplus")

# Initialize FastAPI
app = FastAPI(
    title="Doctor+ Backend",
    description="Medical AI assistant powered by Groq",
    version=BUILD
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq client singleton
_groq_client = None


def get_groq_client() -> AsyncGroq:
    """Get or initialize Groq client with normalized API key."""
    global _groq_client
    if _groq_client is None:
        # Normalize API key: strip whitespace and quotes
        api_key = os.getenv("GROQ_API_KEY", "").strip().strip('"').strip("'")
        
        if not api_key:
            logger.error("GROQ_API_KEY not configured")
            raise ValueError("GROQ_API_KEY not set")
        
        logger.info(f"Initializing Groq client (key length: {len(api_key)})")
        _groq_client = AsyncGroq(api_key=api_key)
    
    return _groq_client


# Request/Response models
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


# Health and version endpoints
@app.get("/health")
async def health():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "build": BUILD}


@app.get("/version")
async def version():
    """Version information endpoint."""
    return {"service": "doctorplus-backend", "build": BUILD}


# Main AI endpoint
@app.post("/doctorplus", response_model=DoctorPlusResponse)
async def doctorplus(request: DoctorPlusRequest):
    """
    Doctor+ AI endpoint with Groq integration.
    
    Processes user symptoms or lab analyses and returns AI-generated
    medical information with safety disclaimers.
    """
    logger.info(
        f"POST /doctorplus: mode={request.mode}, "
        f"text_len={len(request.text)}, has_image={bool(request.image_b64)}"
    )
    
    try:
        # Build medical safety prompt
        system_prompt = """Ты — Доктор+, медицинский информационный ассистент.

СТРОГИЕ ПРАВИЛА:
- Ты НЕ ставишь диагнозы и НЕ назначаешь лечение
- Ты НЕ выписываешь рецепты и НЕ указываешь дозировки
- Ты помогаешь понимать симптомы и анализы простым языком
- Ты даёшь общую информацию, но НЕ заменяешь врача

ОБЯЗАТЕЛЬНО завершай каждый ответ:
⚠️ Важно: Я не врач. Обратитесь к специалисту для точного диагноза и лечения."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.text}
        ]
        
        # Get Groq client
        try:
            client = get_groq_client()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI service not configured"
            )
        
        # Call Groq API with timeout
        try:
            logger.info("Calling Groq API: model=llama-3.1-405b-reasoning")
            
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model="llama-3.1-405b-reasoning",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2048,
                ),
                timeout=60.0
            )
            
            logger.info(f"Groq API success: tokens={response.usage.total_tokens}")
            
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return DoctorPlusResponse(
                answer_md=content,
                usage=usage,
                build=BUILD
            )
            
        except asyncio.TimeoutError:
            logger.error("Groq API timeout (>60s)")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI service timeout"
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Groq API error: {error_msg}")
            
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
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in /doctorplus: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    api_key = os.getenv("GROQ_API_KEY", "").strip().strip('"').strip("'")
    logger.info(f"🚀 Doctor+ Backend starting - Build: {BUILD}")
    logger.info(f"🔑 GROQ_API_KEY configured: {bool(api_key)}")
