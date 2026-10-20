"""
Unit tests for VectorStoreManager and FAISS integration.
"""

from langchain_core.documents import Document


def test_add_and_search_documents(temp_vectorstore):
    user_id = "test_user_alpha"
    docs = [
        Document(page_content="RAG optimizes LLM outputs using retrieved context.", metadata={"source": "rag.pdf", "page": 1}),
        Document(page_content="Gradient descent minimizes loss function in deep neural nets.", metadata={"source": "math.pdf", "page": 4}),
    ]

    indexed_count = temp_vectorstore.add_documents(user_id=user_id, documents=docs)
    assert indexed_count == 2

    # Query matching first document
    results = temp_vectorstore.similarity_search(user_id=user_id, query="What optimizes LLM output?", k=1)
    assert len(results) > 0
    assert "RAG" in results[0].page_content


def test_multi_tenant_isolation(temp_vectorstore):
    user_a = "user_engineering"
    user_b = "user_medical"

    docs_eng = [Document(page_content="Kubernetes orchestrates containerized clusters.", metadata={"source": "k8s.txt"})]
    docs_med = [Document(page_content="Cardiovascular pathology requires echocardiogram screening.", metadata={"source": "med.txt"})]

    temp_vectorstore.add_documents(user_id=user_a, documents=docs_eng)
    temp_vectorstore.add_documents(user_id=user_b, documents=docs_med)

    results_a = temp_vectorstore.similarity_search(user_id=user_a, query="cardiovascular", k=2)
    for r in results_a:
        assert "Cardiovascular" not in r.page_content


def test_clear_user_index(temp_vectorstore):
    user_id = "temp_user"
    docs = [Document(page_content="Temporary notes to be purged.", metadata={"source": "temp.txt"})]
    temp_vectorstore.add_documents(user_id=user_id, documents=docs)

    assert len(temp_vectorstore.similarity_search(user_id=user_id, query="notes")) > 0

    temp_vectorstore.clear_user_index(user_id)
    assert len(temp_vectorstore.similarity_search(user_id=user_id, query="notes")) == 0
