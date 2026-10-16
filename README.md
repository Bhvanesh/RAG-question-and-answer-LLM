# AI Document Q&A API with RAG Evaluation

A production-ready Retrieval Augmented Generation (RAG) API that lets users upload documents and ask natural language questions, with built-in automated evaluation of answer quality using RAGAS.

**Live Demo:** https://awake-clarity-production-859a.up.railway.app/docs

---

## What It Does

Upload a document (PDF or DOCX), ask questions about it in natural language, and get AI-generated answers backed by vector similarity search. Every answer can be automatically evaluated for quality using industry-standard RAG metrics.

```
Upload document → chunked → embedded → stored in ChromaDB
        ↓
Ask question → relevant chunks retrieved → GPT-3.5 generates answer
        ↓
Optional: RAGAS evaluates faithfulness, relevancy, precision, recall
```

---

## Tech Stack

- **API Framework:** FastAPI (async)
- **AI Orchestration:** LangChain
- **LLM:** OpenAI GPT-3.5-turbo
- **Vector Database:** ChromaDB
- **Evaluation:** RAGAS (faithfulness, answer relevancy, context precision, context recall)
- **Database:** PostgreSQL + SQLAlchemy
- **Authentication:** JWT with bcrypt password hashing
- **Containerization:** Docker
- **Deployment:** Railway
- **Language:** Python 3.11

---

## Features

- User registration and login with JWT authentication
- Upload and process PDF and DOCX documents
- RAG-based question answering over uploaded documents
- Automated answer quality evaluation using RAGAS metrics
- Per-document isolated vector storage
- Document ownership validation (users only access their own documents)
- Request logging middleware with timing
- Global exception handling with consistent error responses
- Async routes for non-blocking performance

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

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register a new user |
| POST | `/login` | Login and receive JWT token |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload a PDF or DOCX document |
| GET | `/documents` | List all uploaded documents |

### Question Answering
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/question` | Ask a question about a document |
| POST | `/ask/evaluate` | Ask a question AND get RAGAS evaluation scores |
| GET | `/evaluations` | Retrieve all past evaluation results |

All document and question endpoints require JWT authentication.

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
   ```

5. Run the server
   ```
   uvicorn main:app --reload
   ```

6. Open `http://localhost:8000/docs` for the interactive Swagger UI

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

---

## Architecture Notes

- **Vector storage** is isolated per document in separate ChromaDB directories, ensuring questions about one document never retrieve chunks from another.
- **Embeddings** are generated using OpenAI's embedding model and stored as vectors for semantic similarity search.
- **Chunking** uses recursive character splitting with overlap to preserve context across chunk boundaries.
- **Evaluation** uses RAGAS with an LLM-as-judge approach to score answer quality automatically.

---

## Key Learnings

- Built a complete RAG pipeline from document ingestion through evaluation
- Implemented LLM-as-judge evaluation to quantify RAG quality objectively
- Resolved complex dependency conflicts across RAGAS, LangChain, NumPy, SciPy, and PyArrow by pinning a compatible Python 3.11 stack
- Learned that ephemeral container storage requires persistent volumes or managed vector databases for production vector storage