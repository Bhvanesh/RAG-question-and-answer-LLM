# AI Document Q&A API with Hybrid RAG Search

![CI](https://github.com/Bhvanesh/RAG-question-and-answer-LLM/actions/workflows/ci.yml/badge.svg)

A production-ready Retrieval Augmented Generation (RAG) API that lets users upload documents and ask natural language questions, with built-in hybrid search (BM25 + vector) and automated evaluation of answer quality using RAGAS.

**Live Demo:** https://awake-clarity-production-859a.up.railway.app/docs
**GitHub:** https://github.com/Bhvanesh/RAG-question-and-answer-LLM

---

## What It Does

Upload a document (PDF or DOCX), ask questions about it in natural language, and get AI-generated answers backed by hybrid retrieval — combining semantic vector search with BM25 keyword search for more accurate results. Every answer can be automatically evaluated for quality using industry-standard RAG metrics.

```
Upload document → chunked → embedded → stored in ChromaDB + BM25 index
        ↓
Ask question → two parallel searches:
  Path 1: vector similarity search (semantic)
  Path 2: BM25 keyword search (lexical)
        ↓
Reciprocal Rank Fusion combines both results
        ↓
GPT-4o-mini generates grounded answer with source citations
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
- **Lexical Search:** BM25 (rank-bm25) with Reciprocal Rank Fusion
- **Evaluation:** RAGAS (faithfulness, answer relevancy, context precision, context recall)
- **Database:** PostgreSQL + SQLAlchemy
- **Migrations:** Alembic
- **Authentication:** JWT with bcrypt password hashing
- **Testing:** pytest (5 auth tests, in-memory SQLite, mocked dependencies)
- **CI:** GitHub Actions (runs on every push to main)
- **Containerization:** Docker
- **Deployment:** Railway (auto-deploys on push)
- **Language:** Python 3.11

---

## Features

- User registration and login with JWT authentication
- Upload and process PDF and DOCX documents (UUID filenames, type + size validation)
- **Hybrid retrieval** — BM25 keyword search + vector semantic search combined via Reciprocal Rank Fusion
- RAG-based question answering with source chunk citations and page numbers
- Automated answer quality evaluation using RAGAS metrics
- Batch evaluation endpoint — runs a full golden dataset in one pass
- Per-document isolated vector storage (separate ChromaDB directory per document)
- Document ownership validation (users only access their own documents)
- Request logging middleware with timing
- Global exception handling with consistent error responses
- Database schema migrations with Alembic
- Automated test suite with pytest (5 auth tests, CI on every push)

---

## Hybrid Search Architecture

Standard RAG uses only vector similarity search — it finds semantically similar chunks but can miss exact keyword matches. This project uses **hybrid retrieval** combining two complementary methods:

**Vector search (semantic):** finds chunks with similar *meaning* — handles synonyms and paraphrasing.

**BM25 (lexical):** finds chunks with *exact keyword matches* — handles specific terms, proper nouns, and codes like "AZ-900" or "ChromaDB" that embeddings may not capture well.

**Reciprocal Rank Fusion (RRF):** combines both ranked lists — chunks appearing highly in both searches get boosted, giving more robust retrieval than either method alone.

```
Question → embed → ChromaDB cosine search → top 10 ──┐
Question → tokenize → BM25 keyword search → top 10 ──┤
                                                       ↓
                                         Reciprocal Rank Fusion
                                         score = 1/(rank + 60)
                                                       ↓
                                               Top 3 final chunks
                                                       ↓
                                          LLM generates answer
```

**Why k=10 for candidates but top 3 for LLM:**
Both search methods retrieve k=10 candidates each (20 total). RRF re-ranks all 20 and passes only the top 3 to the LLM. This gives wider search coverage (higher recall) without adding context noise to the LLM (maintains faithfulness).

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
  "answer": "Surya Balakrishnan is a Software Engineer at Accenture...",
  "document": "resume.pdf",
  "evaluation_score": {
    "faithfulness": 1.0,
    "answer_relevancy": 0.767,
    "context_precision": 1.0,
    "context_recall": 1.0,
    "evaluation_latency_seconds": 8.36
  }
}
```

Note: `context_precision` and `context_recall` require `ground_truth` to compute. Without ground truth, these return null and are stored as null in the database — this is correct behavior, not an error.

---

## RAG Benchmark Results

Retrieval configurations were benchmarked against a fixed 12-question golden dataset. See [BENCHMARK.md](BENCHMARK.md) for full methodology and findings.

| Configuration | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|
| k=3, chunk=1000 (baseline) | 0.85 | 0.96 | 0.889 | 0.917 |
| k=5, chunk=1000 | 0.66 | 0.955 | 0.851 | 0.75 |
| k=3, chunk=500 | 0.80 | 0.96 | 0.816 | 0.75 |
| BM25 + vector + RRF (current) | **0.889** | **0.981** | 0.833 | **1.0** |

Bold = improved vs baseline. Context precision (0.833) not bolded — it dropped slightly, as expected when combining two retrieval methods.

Key findings from benchmarking:
- Increasing retrieval depth (k=3→5) degraded faithfulness 22% due to context noise
- Reducing chunk size (1000→500) degraded recall 18% due to fragmented context
- Baseline k=3, chunk=1000 was empirically optimal for pure vector search
- BM25 hybrid search improved faithfulness +4.6%, answer relevancy +2.2%, and achieved perfect recall (1.0) across all 12 questions
- Context precision dropped slightly (-6.3%) — expected tradeoff when combining two retrieval methods
- 0/12 questions failed in both baseline and hybrid configurations

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

All document and question endpoints require a valid JWT token in the Authorization header.

---

## Security

- UUID filenames on upload — prevents path traversal attacks and filename collisions
- File type validation — only PDF and DOCX accepted
- File size limit — 10MB maximum
- Password hashing — bcrypt, hash never returned in API responses
- JWT expiry — tokens expire after 30 minutes
- Generic error messages — internal errors logged server-side, not exposed to clients

---

## Setup

1. Clone the repository
   ```bash
   git clone https://github.com/Bhvanesh/RAG-question-and-answer-LLM.git
   cd RAG-question-and-answer-LLM
   ```

2. Create a Python 3.11 virtual environment
   ```bash
   py -3.11 -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
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
   ```bash
   alembic upgrade head
   ```

6. Start the server
   ```bash
   uvicorn main:app --reload
   ```

7. Open `http://localhost:8000/docs` for the interactive Swagger UI

---

## Running Tests

```bash
pytest tests/ -v
```

Tests use an in-memory SQLite database — no PostgreSQL required. ChromaDB, RAGAS, and LangChain are mocked in `conftest.py` so tests run fast without external dependencies.

```
tests/test_auth.py::test_register_success         PASSED
tests/test_auth.py::test_login_success            PASSED
tests/test_auth.py::test_login_wrong_password     PASSED
tests/test_auth.py::test_protected_route_no_token PASSED
tests/test_auth.py::test_protected_route_valid    PASSED

5 passed
```

---

## Docker

Build and run locally with Docker:

```bash
docker build -t rag-api .
docker run -p 8000:8000 --env-file .env rag-api
```

Note: ChromaDB data is stored inside the container by default. For persistence across restarts, mount a volume:

```bash
docker run -p 8000:8000 --env-file .env \
  -v $(pwd)/chroma_data:/app/chroma_db \
  rag-api
```

---

## Deployment

Deployed on Railway with auto-deploy on push to main. GitHub Actions runs pytest on every push — Railway only deploys if CI passes.

```
git push → GitHub Actions → pytest (5 tests) → Railway auto-deploys
```

**Persistent volume:** ChromaDB is mounted at `/app/chroma_db` on a Railway persistent volume — embeddings survive container restarts and redeployments.

**Migrations:** Alembic runs automatically on startup via Dockerfile CMD:
```dockerfile
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

---

## Usage Flow

1. Register a user via `POST /register`
2. Login via `POST /login` and copy the access token
3. Authorize in Swagger using the token (click the lock icon)
4. Upload a document via `POST /upload`
5. Note the returned `document_id`
6. Ask questions via `POST /question` or `POST /ask/evaluate`
7. Run `POST /batch-evaluate` to benchmark the full golden dataset

---

## Architecture Notes

- **Hybrid retrieval** combines BM25 and ChromaDB vector search via RRF — more robust than either method alone, recovering queries where semantic search fails on exact terms.
- **Vector storage** is isolated per document in separate ChromaDB directories — questions about one document never retrieve chunks from another.
- **Persistent volume** mounted at `/app/chroma_db` on Railway — embeddings survive container restarts and redeployments.
- **Embeddings** generated using OpenAI `text-embedding-ada-002` — stored as 1536-dimensional vectors in ChromaDB.
- **Chunking** uses `RecursiveCharacterTextSplitter` (chunk=1000, overlap=200) — empirically validated as optimal via benchmark.
- **Evaluation** uses RAGAS with GPT-4o-mini as judge — `context_precision` and `context_recall` require `ground_truth` to compute.
- **LLM** configurable via `LLM_MODEL` environment variable — defaults to `gpt-4o-mini`.
- **Migrations** managed with Alembic — schema changes applied safely without data loss.

---

## Key Learnings

- Built a complete RAG pipeline from document ingestion through automated evaluation and benchmarking
- Implemented hybrid retrieval (BM25 + vector + RRF) — discovered that pure semantic search fails on exact proper nouns and codes, which keyword search recovers
- Ran 4 controlled retrieval experiments — found "more retrieval" and "smaller chunks" are not always improvements; validated through measurement
- RAGAS `context_precision` and `context_recall` require `ground_truth` — without it they return null; designed DB schema with nullable columns accordingly
- Ephemeral container storage wipes ChromaDB on redeploy — solved with Railway persistent volumes
- Applied production security: UUID filenames, file validation, bcrypt hashing, generic error messages
- Set up full CI pipeline with pytest and GitHub Actions — tests run automatically on every push
