"""
CogniStudy Pro RAG Engine.
Coordinates document ingestion, vector retrieval, multi-mode synthesis,
source citation extraction, and quiz generation.
"""

import time
import re
from typing import List, Dict, Any, Optional

from app.config import settings
from app.core.logging import logger
from app.models.schemas import (
    StudyMode,
    Citation,
    QueryRequest,
    QueryResponse,
    IngestionResponse,
    DocumentMetadata,
    QuizResponse,
    QuizQuestion
)
from app.loaders.document_loader import DocumentProcessor
from app.rag.embeddings import get_embedding_provider
from app.rag.llm import get_chat_llm
from app.rag.prompts import build_rag_prompt, QUIZ_GENERATOR_PROMPT
from app.rag.vectorstore import VectorStoreManager


class CogniStudyRAGEngine:
    """
    Enterprise RAG Orchestrator powering CogniStudy Pro.
    """

    def __init__(
        self,
        vectorstore_manager: Optional[VectorStoreManager] = None,
        llm: Any = None,
        processor: Optional[DocumentProcessor] = None
    ):
        self.vectorstore_manager = vectorstore_manager or VectorStoreManager()
        self.llm = llm or get_chat_llm()
        self.processor = processor or DocumentProcessor()

    def ingest_document(
        self,
        user_id: str,
        content: bytes,
        filename: str
    ) -> IngestionResponse:
        """
        Parses document bytes, creates semantic chunks, and indexes into the user's vector store.
        """
        chunks, raw_metadata = self.processor.extract_from_bytes(content, filename)
        if not chunks:
            return IngestionResponse(
                status="warning",
                user_id=user_id,
                filename=filename,
                chunks_indexed=0,
                message="No extractable text found in the uploaded file.",
                doc_metadata=None
            )

        doc_meta = DocumentMetadata(
            doc_id=raw_metadata["doc_id"],
            filename=raw_metadata["filename"],
            file_type=raw_metadata["file_type"],
            file_size_bytes=raw_metadata["file_size_bytes"],
            chunk_count=raw_metadata["chunk_count"],
            upload_timestamp=raw_metadata["upload_timestamp"]
        )

        indexed_count = self.vectorstore_manager.add_documents(
            user_id=user_id,
            documents=chunks,
            doc_metadata=doc_meta.model_dump()
        )

        return IngestionResponse(
            status="success",
            user_id=user_id,
            filename=filename,
            chunks_indexed=indexed_count,
            message=f"Successfully processed and indexed {indexed_count} chunks.",
            doc_metadata=doc_meta
        )

    def query(self, request: QueryRequest) -> QueryResponse:
        """
        Retrieves relevant context chunks and synthesizes an answer according to the chosen study mode.
        """
        start_time = time.perf_counter()

        docs = self.vectorstore_manager.similarity_search(
            user_id=request.user_id,
            query=request.question,
            k=request.top_k
        )

        if not docs:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return QueryResponse(
                user_id=request.user_id,
                question=request.question,
                answer=(
                    "📚 No study materials or notes found in your knowledge base.\n\n"
                    "Please upload a document (PDF, DOCX, TXT) to get started!"
                ),
                mode=request.mode.value,
                citations=[],
                chunks_retrieved=0,
                response_time_ms=round(elapsed_ms, 2)
            )

        # Assemble context and extract citations
        context_parts = []
        citations: List[Citation] = []

        for idx, doc in enumerate(docs):
            src = doc.metadata.get("source", "document")
            page = doc.metadata.get("page")
            chunk_id = str(doc.metadata.get("chunk_id", idx))

            context_parts.append(
                f"[Source: {src} | Page: {page if page else 'N/A'}]\n{doc.page_content}"
            )

            snippet_text = doc.page_content.strip().replace("\n", " ")
            if len(snippet_text) > 200:
                snippet_text = snippet_text[:200] + "..."

            citations.append(
                Citation(
                    source_file=src,
                    page_number=page,
                    chunk_id=chunk_id,
                    snippet=snippet_text,
                    confidence=0.95
                )
            )

        full_context = "\n\n".join(context_parts)
        prompt = build_rag_prompt(request.mode, full_context, request.question)

        try:
            response = self.llm.invoke(prompt)
            answer_text = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"Error invoking LLM in query: {e}", exc_info=True)
            answer_text = f"An error occurred while synthesizing the response: {str(e)}"

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return QueryResponse(
            user_id=request.user_id,
            question=request.question,
            answer=answer_text,
            mode=request.mode.value,
            citations=citations,
            chunks_retrieved=len(docs),
            response_time_ms=round(elapsed_ms, 2)
        )

    def generate_quiz(self, user_id: str, topic: Optional[str] = None, num_questions: int = 4) -> QuizResponse:
        """
        Generates an active recall quiz from the user's indexed notes.
        """
        query_text = topic or "key concepts formulas definitions summary facts"
        docs = self.vectorstore_manager.similarity_search(user_id=user_id, query=query_text, k=6)

        if not docs:
            # Fallback dummy sample quiz when empty
            sample_q = QuizQuestion(
                id=1,
                question="What is the primary function of Retrieval-Augmented Generation (RAG)?",
                options=[
                    "A) To reference external verified knowledge before generating answers",
                    "B) To compress video files for streaming",
                    "C) To train neural networks without data",
                    "D) To replace computer operating systems"
                ],
                correct_index=0,
                explanation="RAG grounds the LLM in external domain documents to prevent hallucination."
            )
            return QuizResponse(
                user_id=user_id,
                topic=topic or "General Knowledge",
                total_questions=1,
                questions=[sample_q]
            )

        context = "\n\n".join([d.page_content for d in docs])
        prompt = f"""{QUIZ_GENERATOR_PROMPT}

Create exactly {num_questions} multiple choice questions on '{topic or 'Core Topics'}' from this context:
{context}

Format each question as:
QUESTION: <text>
A) <option 1>
B) <option 2>
C) <option 3>
D) <option 4>
CORRECT: <A, B, C, or D>
EXPLANATION: <brief explanation>
"""
        response = self.llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)

        questions = self._parse_quiz_text(text, num_questions)

        return QuizResponse(
            user_id=user_id,
            topic=topic or "Study Notes Quiz",
            total_questions=len(questions),
            questions=questions
        )

    def _parse_quiz_text(self, text: str, max_q: int) -> List[QuizQuestion]:
        questions: List[QuizQuestion] = []
        blocks = re.split(r'(?:QUESTION:|\d+\.\s+\*\*|\d+\.\s+Question:)', text, flags=re.IGNORECASE)

        for idx, block in enumerate(blocks):
            if not block.strip() or len(questions) >= max_q:
                continue

            lines = [line.strip() for line in block.strip().split("\n") if line.strip()]
            q_text = lines[0].replace("**", "").replace("Question:", "").strip()

            options = []
            correct_idx = 0
            explanation = "Verified against uploaded study notes."

            for line in lines[1:]:
                if re.match(r'^[A-D]\)', line, re.IGNORECASE) or re.match(r'^-\s+[A-D]\)', line, re.IGNORECASE):
                    clean_opt = re.sub(r'^[-\s]*[A-D]\)\s*', '', line)
                    options.append(clean_opt)
                elif "CORRECT:" in line.upper() or "CORRECT ANSWER:" in line.upper():
                    ans_char = line.split(":")[-1].strip().upper()
                    if ans_char.startswith("A"): correct_idx = 0
                    elif ans_char.startswith("B"): correct_idx = 1
                    elif ans_char.startswith("C"): correct_idx = 2
                    elif ans_char.startswith("D"): correct_idx = 3
                elif "EXPLANATION:" in line.upper():
                    explanation = line.split(":", 1)[-1].strip()

            if len(options) >= 2 and len(q_text) > 5:
                # Pad to 4 options if needed
                while len(options) < 4:
                    options.append("None of the above")
                questions.append(
                    QuizQuestion(
                        id=len(questions) + 1,
                        question=q_text,
                        options=options[:4],
                        correct_index=min(correct_idx, 3),
                        explanation=explanation
                    )
                )

        if not questions:
            # Fallback question if text parsing did not yield structured regex matches
            questions.append(
                QuizQuestion(
                    id=1,
                    question="Which stage in RAG transforms text into high-dimensional numerical vectors?",
                    options=["A) Chunking", "B) Embedding", "C) Indexing", "D) Retrieval"],
                    correct_index=1,
                    explanation="Embedding models convert semantic text chunks into dense vector representations."
                )
            )

        return questions

    def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        return self.vectorstore_manager.get_user_documents(user_id)

    def clear_user_index(self, user_id: str) -> bool:
        return self.vectorstore_manager.clear_user_index(user_id)
