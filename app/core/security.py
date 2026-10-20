"""
Security and validation utilities.
"""

import os
import re
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)) -> bool:
    """
    Validates the optional API key header if settings.API_KEY is configured.
    If no API_KEY is set in settings, access is open.
    """
    if not settings.API_KEY:
        return True
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
    return True

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename against path traversal attacks.
    """
    clean_name = os.path.basename(filename)
    clean_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', clean_name)
    return clean_name or "document.pdf"
