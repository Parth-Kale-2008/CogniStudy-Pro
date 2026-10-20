"""
Integration tests for FastAPI REST routes.
"""

import io


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_modes_endpoint(client):
    response = client.get("/api/v1/modes")
    assert response.status_code == 200
    modes = response.json()["modes"]
    assert len(modes) >= 4
    mode_ids = [m["id"] for m in modes]
    assert "student" in mode_ids
    assert "executive" in mode_ids
    assert "researcher" in mode_ids
    assert "exam_cram" in mode_ids


def test_upload_and_query_api(client, sample_txt_bytes):
    # 1. Upload
    files = {"file": ("cloud_arch.txt", io.BytesIO(sample_txt_bytes), "text/plain")}
    data = {"user_id": "api_test_user"}
    upload_res = client.post("/api/v1/upload", files=files, data=data)
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert upload_data["status"] == "success"
    assert upload_data["chunks_indexed"] > 0

    # 2. List Documents
    doc_res = client.get("/api/v1/documents?user_id=api_test_user")
    assert doc_res.status_code == 200
    assert doc_res.json()["total_documents"] >= 1

    # 3. Query
    query_payload = {
        "user_id": "api_test_user",
        "question": "Explain distributed computing frameworks",
        "mode": "student",
        "top_k": 3
    }
    query_res = client.post("/api/v1/query", json=query_payload)
    assert query_res.status_code == 200
    query_data = query_res.json()
    assert "answer" in query_data
    assert len(query_data["citations"]) > 0

    # 4. Generate Quiz
    quiz_payload = {
        "user_id": "api_test_user",
        "num_questions": 2
    }
    quiz_res = client.post("/api/v1/quiz", json=quiz_payload)
    assert quiz_res.status_code == 200
    quiz_data = quiz_res.json()
    assert quiz_data["total_questions"] >= 1

    # 5. Clear Documents
    del_res = client.delete("/api/v1/documents?user_id=api_test_user")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"


def test_upload_empty_file_rejected(client):
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    res = client.post("/api/v1/upload", files=files, data={"user_id": "test"})
    assert res.status_code == 400
