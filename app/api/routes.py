"""
REST API Endpoints for CogniStudy Pro Platform.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Depends, status

from app.config import settings
from app.core.logging import logger
from app.core.security import verify_api_key, sanitize_filename
from app.models.schemas import (
    QueryRequest,
    QueryResponse,
    IngestionResponse,
    DocumentListResponse,
    DocumentMetadata,
    QuizRequest,
    QuizResponse,
    HealthResponse,
    StudyMode
)
from app.rag.engine import CogniStudyRAGEngine
from app.services.telegram_service import TelegramService

router = APIRouter()

# Global instances initialized on demand
_engine_instance: Optional[CogniStudyRAGEngine] = None
_telegram_instance: Optional[TelegramService] = None


def get_rag_engine() -> CogniStudyRAGEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = CogniStudyRAGEngine()
    return _engine_instance


def get_telegram_service() -> TelegramService:
    global _telegram_instance
    if _telegram_instance is None:
        _telegram_instance = TelegramService(rag_engine=get_rag_engine())
    return _telegram_instance


# --- SYSTEM & HEALTH ---

@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check(engine: CogniStudyRAGEngine = Depends(get_rag_engine)):
    """
    Returns platform health, version metadata, and active tenant index count.
    """
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        llm_provider=settings.DEFAULT_LLM_PROVIDER,
        embedding_provider=settings.EMBEDDING_PROVIDER,
        indexed_tenants=engine.vectorstore_manager.count_tenants()
    )


@router.get("/modes", tags=["Study Modes"])
def list_study_modes():
    """
    Lists available AI study & analysis personas.
    """
    return {
        "modes": [
            {
                "id": StudyMode.STUDENT.value,
                "name": "AI Professor / Student Mode",
                "badge": "🎓 Student",
                "description": "Explains concepts simply with analogies, step-by-step logic, and definitions."
            },
            {
                "id": StudyMode.EXECUTIVE.value,
                "name": "Executive & Professional Mode",
                "badge": "💼 Executive",
                "description": "Concise executive summary, key findings, strategic takeaways, and next actions."
            },
            {
                "id": StudyMode.RESEARCHER.value,
                "name": "Deep Researcher & Scholar Mode",
                "badge": "🔬 Researcher",
                "description": "Scholarly precision with exact quotes, empirical evidence, and source citations."
            },
            {
                "id": StudyMode.EXAM_CRAM.value,
                "name": "Exam Cram & Active Recall Mode",
                "badge": "⚡ Exam Prep",
                "description": "High-yield test facts, memory mnemonics, and rapid-fire active recall questions."
            }
        ]
    }


# --- INGESTION & DOCUMENTS ---

@router.post(
    "/upload",
    response_model=IngestionResponse,
    tags=["Ingestion"],
    dependencies=[Depends(verify_api_key)]
)
async def upload_document(
    file: UploadFile = File(..., description="Document file (PDF, DOCX, TXT, MD, CSV)"),
    user_id: str = Form("default", description="Workspace or user ID"),
    engine: CogniStudyRAGEngine = Depends(get_rag_engine)
):
    """
    Ingests and indexes an uploaded document into the user's isolated vector store.
    """
    safe_filename = sanitize_filename(file.filename or "uploaded_document")
    content = await file.read()

    # File size validation
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty"
        )

    result = engine.ingest_document(
        user_id=user_id,
        content=content,
        filename=safe_filename
    )

    return result


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    tags=["Documents"],
    dependencies=[Depends(verify_api_key)]
)
def list_user_documents(
    user_id: str = "default",
    engine: CogniStudyRAGEngine = Depends(get_rag_engine)
):
    """
    Lists all indexed documents and chunk statistics for a specified user or tenant.
    """
    raw_docs = engine.get_user_documents(user_id)
    doc_models = [
        DocumentMetadata(
            doc_id=d.get("doc_id", "unknown"),
            filename=d.get("filename", "unknown"),
            file_type=d.get("file_type", ""),
            file_size_bytes=d.get("file_size_bytes", 0),
            chunk_count=d.get("chunk_count", 0),
            upload_timestamp=d.get("upload_timestamp", "")
        )
        for d in raw_docs
    ]
    total_chunks = sum(d.chunk_count for d in doc_models)

    return DocumentListResponse(
        user_id=user_id,
        total_documents=len(doc_models),
        total_chunks=total_chunks,
        documents=doc_models
    )


@router.delete(
    "/documents",
    tags=["Documents"],
    dependencies=[Depends(verify_api_key)]
)
def clear_user_documents(
    user_id: str = "default",
    engine: CogniStudyRAGEngine = Depends(get_rag_engine)
):
    """
    Purges a user's entire knowledge base index and document history.
    """
    success = engine.clear_user_index(user_id)
    return {
        "status": "success" if success else "error",
        "user_id": user_id,
        "message": f"Successfully cleared knowledge index for user '{user_id}'."
    }


# --- RAG QUERY & QUIZ GENERATION ---

@router.post(
    "/query",
    response_model=QueryResponse,
    tags=["RAG Engine"],
    dependencies=[Depends(verify_api_key)]
)
def query_knowledge_base(
    request: QueryRequest,
    engine: CogniStudyRAGEngine = Depends(get_rag_engine)
):
    """
    Executes a contextual RAG search and synthesizes an answer with citations.
    """
    if not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question query cannot be empty"
        )
    return engine.query(request)


@router.post(
    "/quiz",
    response_model=QuizResponse,
    tags=["Active Recall"],
    dependencies=[Depends(verify_api_key)]
)
def generate_active_recall_quiz(
    request: QuizRequest,
    engine: CogniStudyRAGEngine = Depends(get_rag_engine)
):
    """
    Generates an active recall multiple-choice quiz derived strictly from uploaded notes.
    """
    return engine.generate_quiz(
        user_id=request.user_id,
        topic=request.topic,
        num_questions=request.num_questions
    )


# --- TELEGRAM 24/7 WEBHOOK ---

@router.post("/telegram-webhook", tags=["Telegram Integration"])
async def telegram_webhook(
    request: Request,
    tg_service: TelegramService = Depends(get_telegram_service)
):
    """
    Webhook endpoint receiving incoming updates from the Telegram Bot API.
    """
    try:
        payload = await request.json()
    except Exception:
        return {"ok": True}

    return await tg_service.handle_update(payload)


@router.get("/telegram-info", tags=["Telegram Integration"])
def telegram_info():
    """
    Diagnostics endpoint for Telegram bot status.
    """
    token_configured = bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_TOKEN.strip())
    masked_token = (
        settings.TELEGRAM_BOT_TOKEN[:6] + "..." + settings.TELEGRAM_BOT_TOKEN[-4:]
        if token_configured and len(settings.TELEGRAM_BOT_TOKEN) > 10
        else "NOT_SET"
    )
    return {
        "telegram_configured": token_configured,
        "token_preview": masked_token,
        "webhook_url": settings.TELEGRAM_WEBHOOK_URL or "Auto/None",
        "instructions": (
            "To activate 24/7 Telegram bot, set TELEGRAM_BOT_TOKEN in .env and point "
            "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<YOUR_SERVER_URL>/telegram-webhook"
        )
    }
