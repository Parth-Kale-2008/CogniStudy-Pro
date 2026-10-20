"""
Unit tests for Telegram Bot webhook and command routing.
"""

import pytest
from app.services.telegram_service import TelegramService


@pytest.mark.asyncio
async def test_telegram_start_command(rag_engine):
    service = TelegramService(rag_engine=rag_engine)
    # Stub send_message
    sent_messages = []

    async def mock_send(chat_id, text):
        sent_messages.append({"chat_id": chat_id, "text": text})
        return True

    service.send_message = mock_send

    payload = {
        "update_id": 1001,
        "message": {
            "chat": {"id": 12345},
            "text": "/start"
        }
    }

    result = await service.handle_update(payload)
    assert result == {"ok": True}
    assert len(sent_messages) == 1
    assert "Welcome to CogniStudy Pro" in sent_messages[0]["text"]


@pytest.mark.asyncio
async def test_telegram_mode_command(rag_engine):
    service = TelegramService(rag_engine=rag_engine)
    sent_messages = []

    async def mock_send(chat_id, text):
        sent_messages.append({"chat_id": chat_id, "text": text})
        return True

    service.send_message = mock_send

    payload = {
        "update_id": 1002,
        "message": {
            "chat": {"id": 12345},
            "text": "/mode executive"
        }
    }

    result = await service.handle_update(payload)
    assert result == {"ok": True}
    assert len(sent_messages) == 1
    assert "EXECUTIVE" in sent_messages[0]["text"]


@pytest.mark.asyncio
async def test_telegram_query(rag_engine, sample_txt_bytes):
    service = TelegramService(rag_engine=rag_engine)
    sent_messages = []

    async def mock_send(chat_id, text):
        sent_messages.append({"chat_id": chat_id, "text": text})
        return True

    service.send_message = mock_send

    # Ingest document first
    rag_engine.ingest_document(user_id="tg_99999", content=sample_txt_bytes, filename="notes.txt")

    payload = {
        "update_id": 1003,
        "message": {
            "chat": {"id": 99999},
            "text": "Explain distributed computing"
        }
    }

    result = await service.handle_update(payload)
    assert result == {"ok": True}
    assert len(sent_messages) == 1
    assert sent_messages[0]["text"] is not None


@pytest.mark.asyncio
async def test_empty_update(rag_engine):
    service = TelegramService(rag_engine=rag_engine)
    result = await service.handle_update({})
    assert result == {"ok": True}
