# AI Document Q&A API with RAG Evaluation

![CI](https://github.com/Bhvanesh/RAG-question-and-answer-LLM/actions/workflows/ci.yml/badge.svg)

A production-ready Retrieval Augmented Generation (RAG) API that lets users upload documents and ask natural language questions, with built-in automated evaluation of answer quality using RAGAS.

**Live Demo:** https://awake-clarity-production-859a.up.railway.app/docs  
**GitHub:** https://github.com/Bhvanesh/RAG-question-and-answer-LLM

---

## What It Does

Upload a document (PDF or DOCX), ask questions about it in natural language, and get AI-generated answers backed by vector similarity search. Every answer can be automatically evaluated for quality using industry-standard RAG metrics.

```
Upload document → chunked → embedded → stored in ChromaDB
        ↓
Ask question → relevant chunks retrieved → GPT generates answer
        ↓
Optional: RAGAS evaluates faithfulness, relevancy, precision, recall
        ↓
Batch evaluation: run golden dataset → aggregate metrics → benchmark configs
```

---

## Tech Stack

- **API Framework:** FastAPI (async)
- **AI Orchestration:** LangChain
- **LLM:** OpenAI GPT-4o-mini (configurable via LLM_MODEL env var)
- **Vector Database:** ChromaDB (persistent volume on Railway)
- **Evaluation:** RAGAS (faithfulness, answer relevancy, context precision, context recall)
- **Database:** PostgreSQL + SQLAlchemy
- **Migrations:** Alembic
- **Authentication:** JWT with bcrypt password hashing
- **Testing:** pytest with in-memory SQLite
- **CI:** GitHub Actions
- **Containerization:** Docker
- **Deployment:** Railway
- **Language:** Python 3.11

---

## Features

- User registration and login with JWT authentication
- Upload and process PDF and DOCX documents (UUID filenames, type + size validation)
- RAG-based question answering with source chunk citations and page numbers
- Automated answer quality evaluation using RAGAS metrics
- Batch evaluation endpoint — runs a full golden dataset in one pass
- Per-document isolated vector storage with Railway persistent volumes
- Document ownership validation (users only access their own documents)
- Request logging middleware with timing
- Global exception handling with consistent error responses
- Database schema migrations with Alembic
- Automated test suite with pytest (5 auth tests, CI on every push)

---

## Evaluation Metrics

This project goes beyond basic RAG by measuring answer quality automatically:

- **Faithfulness** — Is the answer grounded in the retrieved document, or hallucinated?
- **Answer Relevancy** — Is the answer actually relevant to the question asked?
- **Context Precision** — Were the retrieved chunks useful for answering?
- **Context Recall** — Did retrieval find all the relevant information? (requires ground truth)

Example evaluation output:

```json
{
  "question": "Who is Surya Balakrishnan?",
  "answer": "Surya Balakrishnan is a Full-Stack Engineer and AI Consultant...",
  "document": "resume.pdf",
  "evaluation_score": {
    "faithfulness": 1.0,
    "answer_relevancy": 0.91,
    "context_precision": 1.0,
    "context_recall": 1.0,
    "evaluation_latency_seconds": 8.36
  }
}
```

---

## RAG Benchmark Results

Retrieval configurations were benchmarked against a fixed 12-question golden dataset. See [BENCHMARK.md](BENCHMARK.md) for full methodology and findings.

| Configuration | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|
| **k=3, chunk=1000** (chosen) | **0.85** | 0.96 | **0.889** | **0.917** |
| k=5, chunk=1000 | 0.66 | 0.955 | 0.851 | 0.75 |
| k=3, chunk=500 | 0.80 | 0.96 | 0.816 | 0.75 |

Key finding: increasing retrieval depth (k=3→5) degraded faithfulness 22%. Reducing chunk size (1000→500) degraded recall 18%. The baseline configuration was empirically optimal.

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register a new user |
| POST | `/login` | Login and receive JWT token |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload a PDF or DOCX document (max 10MB) |
| GET | `/documents` | List all uploaded documents |

### Question Answering
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/question` | Ask a question, get answer with source citations |
| POST | `/ask/evaluate` | Ask a question AND get RAGAS evaluation scores |
| GET | `/evaluations` | Retrieve all past evaluation results |
| POST | `/batch-evaluate` | Run full golden dataset evaluation |

All document and question endpoints require JWT authentication.

---

## Security

- UUID filenames on upload — prevents path traversal attacks and filename collisions
- File type validation — only PDF and DOCX accepted
- File size limit — 10MB maximum
- Password hashing — bcrypt, hash never returned in API responses
- JWT expiry — tokens expire after 30 minutes
- Generic error messages — internal errors logged, not exposed to clients

---

## Setup

1. Clone the repository
   ```
   git clone https://github.com/Bhvanesh/RAG-question-and-answer-LLM.git
   cd RAG-question-and-answer-LLM
   ```

2. Create a Python 3.11 virtual environment
   ```
   py -3.11 -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file
   ```
   DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/dbname
   OPENAI_API_KEY=your-openai-key
   SECRET_KEY=your-secret-key
   LLM_MODEL=gpt-4o-mini
   ```

5. Run database migrations
   ```
   alembic upgrade head
   ```

6. Run the server
   ```
   uvicorn main:app --reload
   ```

7. Open `http://localhost:8000/docs` for the interactive Swagger UI

---

## Running Tests

```
pytest tests/ -v
```

Tests use an in-memory SQLite database — no PostgreSQL required. Heavy dependencies (ChromaDB, RAGAS) are mocked so tests run fast and without GPU/ML dependencies.

---

## Docker

Build and run with Docker Compose (includes PostgreSQL):

```
docker-compose up --build
```

---

## Usage Flow

1. Register a user via `/register`
2. Login via `/login` and copy the access token
3. Authorize in Swagger using the token
4. Upload a document via `/upload`
5. Note the returned `document_id`
6. Ask questions via `/question` or `/ask/evaluate`
7. Run `/batch-evaluate` to benchmark the full golden dataset

---

## Architecture Notes

- **Vector storage** is isolated per document in separate ChromaDB directories — questions about one document never retrieve chunks from another.
- **Persistent volume** mounted at `/app/chroma_db` on Railway — embeddings survive container restarts and redeployments.
- **Embeddings** are generated using OpenAI's embedding model and stored as vectors for semantic similarity search.
- **Chunking** uses recursive character splitting (chunk=1000, overlap=200) — empirically validated as optimal via benchmark.
- **Evaluation** uses RAGAS with an LLM-as-judge approach to score answer quality automatically.
- **LLM** is configurable via `LLM_MODEL` environment variable — defaults to `gpt-4o-mini`.
- **Migrations** managed with Alembic — schema changes are applied safely without data loss.

---

## Key Learnings

- Built a complete RAG pipeline from document ingestion through automated evaluation and benchmarking
- Implemented LLM-as-judge evaluation (RAGAS) to quantify RAG quality objectively across a 12-question golden dataset
- Ran controlled experiments across retrieval configurations — found that "more retrieval" and "smaller chunks" are not always improvements; validated through measurement
- Resolved complex dependency conflicts across RAGAS, LangChain, NumPy, SciPy, and PyArrow by pinning a compatible Python 3.11 stack
- Learned that ephemeral container storage wipes vector databases on redeploy — solved with Railway persistent volumes
- Applied production security practices: UUID upload filenames, file validation, bcrypt hashing, generic error messages
- Set up full CI pipeline with pytest and GitHub Actions — tests run automatically on every push
