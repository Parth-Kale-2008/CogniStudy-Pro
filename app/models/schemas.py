"""
Pydantic Schemas for CogniStudy Pro Platform.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class StudyMode(str, Enum):
    STUDENT = "student"
    EXECUTIVE = "executive"
    RESEARCHER = "researcher"
    EXAM_CRAM = "exam_cram"
    QUIZ_GENERATOR = "quiz_generator"


class Citation(BaseModel):
    source_file: str
    page_number: Optional[int] = None
    chunk_id: Optional[str] = None
    snippet: str
    confidence: Optional[float] = 1.0


class QueryRequest(BaseModel):
    user_id: str = Field(default="default", description="User or workspace ID")
    question: str = Field(..., min_length=1, description="Question or prompt to answer")
    mode: StudyMode = Field(default=StudyMode.STUDENT, description="Target study mode")
    top_k: int = Field(default=4, ge=1, le=20, description="Number of context chunks to retrieve")
    stream: bool = Field(default=False, description="Whether to stream response")


class QueryResponse(BaseModel):
    user_id: str
    question: str
    answer: str
    mode: str
    citations: List[Citation] = Field(default_factory=list)
    chunks_retrieved: int = 0
    response_time_ms: float = 0.0


class DocumentMetadata(BaseModel):
    doc_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    chunk_count: int
    upload_timestamp: str


class IngestionResponse(BaseModel):
    status: str
    user_id: str
    filename: str
    chunks_indexed: int
    message: str
    doc_metadata: Optional[DocumentMetadata] = None


class DocumentListResponse(BaseModel):
    user_id: str
    total_documents: int
    total_chunks: int
    documents: List[DocumentMetadata] = Field(default_factory=list)


class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str]
    correct_index: int
    explanation: str


class QuizRequest(BaseModel):
    user_id: str = "default"
    num_questions: int = Field(default=4, ge=1, le=10)
    topic: Optional[str] = None


class QuizResponse(BaseModel):
    user_id: str
    topic: str
    total_questions: int
    questions: List[QuizQuestion]


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str
    llm_provider: str
    embedding_provider: str
    indexed_tenants: int = 0
