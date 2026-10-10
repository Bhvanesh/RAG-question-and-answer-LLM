# AI Document Q&A API

A production-ready REST API that allows users to upload documents 
and ask AI-powered questions about them using LangChain and OpenAI.

## Tech Stack
- FastAPI
- PostgreSQL
- SQLAlchemy
- LangChain
- ChromaDB
- OpenAI GPT-3.5
- JWT Authentication
- Python

## Features
- User registration and login with JWT authentication
- Upload PDF and DOCX documents
- AI-powered Q&A on uploaded documents
- Vector similarity search with ChromaDB
- Request logging middleware
- Async routes
- Global exception handling

## How It Works
1. User uploads a document
2. Document is split into chunks and stored as embeddings in ChromaDB
3. User asks a question
4. ChromaDB finds relevant chunks using vector similarity search
5. OpenAI GPT generates answer from relevant chunks

## Endpoints

### Auth
- POST /register → Register new user
- POST /login → Login and get JWT token

### Documents
- POST /upload → Upload PDF or DOCX document (protected)
- GET /documents → List all uploaded documents (protected)

### Q&A
- POST /question → Ask question about a document (protected)

## Setup

1. Clone the repository
2. Create virtual environment:
   python -m venv venv
3. Activate:
   venv\Scripts\activate
4. Install packages:
   pip install -r requirements.txt
5. Create .env file:
   DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/dbname
   OPENAI_API_KEY=your-openai-key
   SECRET_KEY=your-secret-key
6. Run:
   uvicorn main:app --reload

## Example

Upload your resume and ask:
- "What are the certifications listed?"
- "What is the candidate's work experience?"
- "What skills does this person have?"
