"""
Unit tests for CogniStudyRAGEngine (ingestion, study modes, citations, quizzes).
"""

from app.models.schemas import QueryRequest, StudyMode


def test_ingest_and_query_flow(rag_engine, sample_pdf_bytes):
    user_id = "scholar_101"

    # 1. Ingestion
    ingest_res = rag_engine.ingest_document(
        user_id=user_id,
        content=sample_pdf_bytes,
        filename="lecture1.pdf"
    )
    assert ingest_res.status == "success"
    assert ingest_res.chunks_indexed >= 2

    # 2. Query in Student Mode
    req_student = QueryRequest(
        user_id=user_id,
        question="What is RAG?",
        mode=StudyMode.STUDENT
    )
    res_student = rag_engine.query(req_student)
    assert res_student.answer is not None
    assert len(res_student.citations) > 0
    assert res_student.citations[0].source_file == "lecture1.pdf"

    # 3. Query in Executive Mode
    req_exec = QueryRequest(
        user_id=user_id,
        question="What is the strategic value of vector embeddings?",
        mode=StudyMode.EXECUTIVE
    )
    res_exec = rag_engine.query(req_exec)
    assert res_exec.mode == "executive"
    assert res_exec.answer is not None


def test_query_empty_knowledge_base(rag_engine):
    req = QueryRequest(
        user_id="empty_user_999",
        question="What is quantum gravity?",
        mode=StudyMode.STUDENT
    )
    res = rag_engine.query(req)
    assert "No study materials or notes found" in res.answer
    assert len(res.citations) == 0


def test_quiz_generation(rag_engine, sample_txt_bytes):
    user_id = "quiz_taker"
    rag_engine.ingest_document(user_id=user_id, content=sample_txt_bytes, filename="distributed.txt")

    quiz_res = rag_engine.generate_quiz(user_id=user_id, num_questions=2)
    assert quiz_res.total_questions >= 1
    assert len(quiz_res.questions[0].options) == 4
    assert 0 <= quiz_res.questions[0].correct_index <= 3
