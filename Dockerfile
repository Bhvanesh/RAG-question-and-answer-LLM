FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

COPY . .

RUN mkdir -p uploads chroma_db

EXPOSE 8000

CMD ["sh", "-c", "alembic stamp head && alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --loop asyncio"]