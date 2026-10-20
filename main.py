"""
CogniStudy Pro™ — Enterprise Multi-Modal RAG Platform & 24/7 Agent.
Root FastAPI application entry point.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.config import settings
from app.core.logging import logger
from app.api.routes import router as api_router, get_rag_engine, get_telegram_service
from app.models.schemas import QueryRequest, StudyMode


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    logger.info(f"LLM Provider: {settings.DEFAULT_LLM_PROVIDER} | Embedding Provider: {settings.EMBEDDING_PROVIDER}")
    os.makedirs(settings.INDEX_STORAGE_DIR, exist_ok=True)
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME} gracefully.")


app = FastAPI(
    title=f"{settings.APP_NAME} — Enterprise RAG Platform",
    version=settings.APP_VERSION,
    description=(
        "Enterprise-grade multi-modal Retrieval-Augmented Generation (RAG) platform "
        "featuring specialized study & executive personas, multi-format ingestion, "
        "active recall quiz generation, and 24/7 Telegram agent orchestration."
    ),
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Router under prefix
app.include_router(api_router, prefix=settings.API_PREFIX)

# Also include root-level aliases for legacy compatibility
app.include_router(api_router)

# Mount Static Files (Web Application UI)
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", tags=["Web Interface"])
def index():
    """
    Serves the modern CogniStudy Pro Web Dashboard.
    """
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse(
        content={
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "active",
            "docs_url": "/docs"
        }
    )


# --- Legacy Backward-Compatible Helper Functions ---

def process_and_index_pdf(user_id: str, content: bytes) -> int:
    """Legacy helper function preserved for backwards compatibility."""
    engine = get_rag_engine()
    res = engine.ingest_document(user_id=user_id, content=content, filename="document.pdf")
    return res.chunks_indexed


def query_rag(user_id: str, question: str) -> str:
    """Legacy helper function preserved for backwards compatibility."""
    engine = get_rag_engine()
    req = QueryRequest(user_id=user_id, question=question, mode=StudyMode.STUDENT)
    res = engine.query(req)
    return res.answer


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
