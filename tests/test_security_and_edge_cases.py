"""
Unit tests for security, edge cases, and filename sanitization.
"""

from app.core.security import sanitize_filename, verify_api_key
from app.config import settings
import pytest
from fastapi import HTTPException


def test_sanitize_filename_traversal():
    malicious = "../../etc/passwd"
    clean = sanitize_filename(malicious)
    assert "/" not in clean
    assert "\\" not in clean
    assert clean == "passwd"


def test_sanitize_filename_special_chars():
    dirty = "My Lecture & Notes (2024)!?.pdf"
    clean = sanitize_filename(dirty)
    assert clean.endswith(".pdf")
    assert not any(c in clean for c in ["&", "?", "!"])


def test_verify_api_key_when_disabled():
    settings.API_KEY = None
    assert verify_api_key(None) is True


def test_verify_api_key_when_enabled():
    settings.API_KEY = "secret_vendor_token_123"
    assert verify_api_key("secret_vendor_token_123") is True

    with pytest.raises(HTTPException) as exc_info:
        verify_api_key("wrong_token")
    assert exc_info.value.status_code == 401

    # Reset
    settings.API_KEY = None
