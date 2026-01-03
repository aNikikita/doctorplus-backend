"""
Configuration management for Doctor+ Backend
Loads and validates environment variables
"""

import os
from typing import List
from enum import Enum


class Environment(str, Enum):
    """Deployment environment"""
    DEV = "dev"
    PROD = "prod"


class Config:
    """Application configuration from environment variables"""
    
    # Build version
    BUILD: str = "2026-01-02-render-a"
    
    # Environment
    ENVIRONMENT: Environment = Environment(os.getenv("ENVIRONMENT", "dev").lower())
    
    # Groq API
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip().strip('"').strip("'")
    
    # Groq models
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_FALLBACK_MODEL: str = os.getenv("GROQ_FALLBACK_MODEL", "llama-3.1-8b-instant")
    
    # Client authentication
    DOCTORPLUS_API_KEY: str = os.getenv("DOCTORPLUS_API_KEY", "").strip().strip('"').strip("'")
    REQUIRE_LEGACY_AUTH: bool = os.getenv("REQUIRE_LEGACY_AUTH", "0") == "1"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        origin.strip() 
        for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") 
        if origin.strip()
    ]
    
    # Rate limiting
    DOCTORPLUS_RPM: int = int(os.getenv("DOCTORPLUS_RPM", "30"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_USER_SNIPPET: bool = os.getenv("LOG_USER_SNIPPET", "0") == "1"
    
    # Debug
    DEBUG_ENDPOINTS: bool = os.getenv("DEBUG_ENDPOINTS", "0") == "1"
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        
        # GROQ_API_KEY always required
        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is required")
        
        # DOCTORPLUS_API_KEY required in production
        if cls.ENVIRONMENT == Environment.PROD and not cls.DOCTORPLUS_API_KEY:
            errors.append("DOCTORPLUS_API_KEY is required in production")
        
        # ALLOWED_ORIGINS must be explicit in production
        if cls.ENVIRONMENT == Environment.PROD and not cls.ALLOWED_ORIGINS:
            errors.append("ALLOWED_ORIGINS must be explicitly set in production (no wildcard)")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    @classmethod
    def get_cors_origins(cls) -> List[str]:
        """Get CORS origins based on environment"""
        if cls.ALLOWED_ORIGINS:
            return cls.ALLOWED_ORIGINS
        elif cls.ENVIRONMENT == Environment.DEV:
            return ["*"]
        else:
            return []  # Production without explicit origins = no CORS
    
    @classmethod
    def is_auth_required(cls, path: str) -> bool:
        """Check if authentication is required for a path"""
        # /v1 endpoints require auth (except health/version)
        if path.startswith("/v1/"):
            if path in ["/v1/health", "/v1/version", "/v1"]:
                return False
            return True
        
        # Legacy endpoints
        if path == "/doctorplus" and cls.REQUIRE_LEGACY_AUTH:
            return True
        
        return False


# Validate on import
Config.validate()