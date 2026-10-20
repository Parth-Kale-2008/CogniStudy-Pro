# 🧠 CogniStudy Pro™ (formerly StudyMate)
### *Enterprise Multi-Modal RAG Document Intelligence & 24/7 Autonomous Study Platform*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-Enabled-1C3C3C?style=for-the-badge)](https://langchain.com)
[![FAISS Vector Store](https://img.shields.io/badge/Vector_DB-FAISS-0468FF?style=for-the-badge)](https://github.com/facebookresearch/faiss)
[![Tests](https://img.shields.io/badge/Tests-100%25%20Passing%20(22%2F22)-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](tests/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](Dockerfile)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

---

## 🌟 Overview & Commercial Highlights

**CogniStudy Pro™** is a turnkey, production-grade **Retrieval-Augmented Generation (RAG)** platform designed to transform dense documents (PDFs, DOCX, TXT, Markdown, CSV) into interactive, factual, and verified knowledge bases.

Engineered for **EdTech platforms, enterprise research teams, universities, and commercial AI vendors**, it provides a multi-channel interface:
1. 🖥️ **Modern Glassmorphism Web App:** Live drag-and-drop document ingestion, citation inspection drawer, and active recall practice quiz modal.
2. 🤖 **24/7 Telegram AI Assistant:** Cloud webhook supporting document uploads, interactive commands (`/mode`, `/quiz`, `/stats`, `/clear`), and multi-turn study sessions.
3. ⚡ **High-Performance REST API:** OpenAPI/Swagger compliant backend with multi-tenant index isolation.
4. 💻 **Interactive CLI Assistant:** Dedicated terminal interface for rapid local querying and testing.

---

## 🎓 4 Specialized AI Study & Analysis Personas

| Study Mode | Key Strength | Ideal Audience | Output Structure |
|---|---|---|---|
| **🎓 Professor / Student** | Socratic explanations & analogies | High school, undergraduate, self-learners | Core concept, step-by-step logic, everyday analogy, key takeaways |
| **💼 Executive / Pro** | High-level strategic synthesis | Business leaders, analysts, managers | TL;DR summary, quantitative findings, risk factors, actionable next steps |
| **🔬 Deep Researcher** | Scholarly rigor & exact quotes | Graduate researchers, scientists, legal pros | Theoretical framework, primary quote citations, methodological nuances |
| **⚡ Exam Cram Coach** | Active recall & high-yield facts | Students preparing for exams, certifications | High-probability test facts, mnemonics, rapid-fire Q&A, examiner red flags |

---

## 📸 Key Capabilities

* 📄 **Multi-Format Semantic Parser:** Ingests `.pdf` (with page-level metadata via PyMuPDF/PyPDF), Word `.docx` (paragraphs & tables), `.txt`, `.md`, and `.csv`.
* 📌 **Page-Level Source Citations:** Every synthesized answer provides verified references with page numbers and exact quote snippets. Click any citation to inspect the source text.
* 🎯 **Dynamic Quiz & Flashcard Generator:** Generates 4-choice interactive active recall quizzes with instant scoring and grounded explanations directly from uploaded notes.
* 🏢 **Multi-Tenant Index Isolation:** Each user or team has a sandboxed FAISS vector store (`faiss_data/{user_id}/`).
* 🔌 **Multi-Provider LLM & Zero-Cost Offline Fallback:** Native support for OpenAI (`gpt-4o-mini`, `gpt-4o`), Groq, Anthropic, Ollama, plus a built-in deterministic mock provider for zero-cost offline testing and demonstrations!
* 🐳 **Containerized & Production Ready:** Dockerfile, Docker Compose, automated GitHub Actions CI testing, and health check probes.

---

## 🏗️ Architecture

```text
[ Web UI / Telegram Bot / REST Client / CLI ]
                      │
                      ▼
            [ FastAPI API Gateway ]
          (CORS, Auth, Sanitization)
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
[ Ingestion Pipeline ]      [ Multi-Persona RAG Engine ]
  ├─ PDF / DOCX / TXT         ├─ Similarity Vector Search (FAISS)
  ├─ Recursive Chunker        ├─ Multi-Persona Prompt Engineering
  ├─ Embeddings Generator     ├─ LLM Response Synthesis
  └─ Tenant Vector Index      └─ Citation & Page Attributor
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
* Python 3.10, 3.11, or 3.12
* (Optional) Docker & Docker Compose

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/Parth-Kale-2008/CogniStudy-Pro.git
cd CogniStudy-Pro

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the template and configure your keys:
```bash
cp .env.example .env
```
*(Note: If you don't provide an `OPENAI_API_KEY`, CogniStudy Pro automatically runs in deterministic mock mode for offline demonstration!)*

### 4. Run the Automated Tests (100% Pass)
```bash
python -m pytest
```
```text
======================= 22 passed in 1.95s =======================
```

### 5. Launch the Web Application
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser and navigate to:
* **Interactive Web Dashboard:** [http://localhost:8000](http://localhost:8000)
* **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check Probe:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 🐳 Docker Deployment

Run the entire platform in a container with one command:
```bash
docker-compose up -d --build
```

---

## 🤖 24/7 Telegram Bot Commands

When connected to Telegram via webhook:
* `/start` — Welcome guide and quick start instructions
* `/help` — How to upload files and execute queries
* `/mode <student|executive|researcher|exam_cram>` — Switch active study persona
* `/modes` — View descriptions of all 4 study modes
* `/quiz [topic]` — Formulate an instant active recall practice quiz from notes
* `/stats` — View indexed document count and total semantic chunks
* `/clear` — Purge uploaded notes and reset conversation memory

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health, uptime, version, and tenant index count |
| `GET` | `/api/v1/modes` | List all available study personas |
| `POST` | `/api/v1/upload` | Ingest and index a document (`multipart/form-data`) |
| `POST` | `/api/v1/query` | Execute a contextual RAG query with citations |
| `POST` | `/api/v1/quiz` | Generate an active recall quiz from indexed notes |
| `GET` | `/api/v1/documents` | List indexed documents and chunk statistics |
| `DELETE` | `/api/v1/documents` | Purge tenant vector index and history |
| `POST` | `/telegram-webhook` | Telegram Bot update handler |
| `GET` | `/telegram-info` | Telegram Bot diagnostics and setup helper |

---

## 💼 DataVendor.ai Commercial Listing & Valuation

Are you looking to acquire, license, or sell this platform?
See [DATAVENDOR_LISTING.md](DATAVENDOR_LISTING.md) for the complete turn-key sales pitch, buyer handover checklist, monetization roadmap ($1,750–$3,500 valuation), and commercial rights breakdown.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — free for personal, educational, and commercial use.
