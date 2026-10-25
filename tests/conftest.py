import os
import sys
from unittest.mock import MagicMock

# This runs before ANYTHING else in tests
# Set env vars before database.py imports and creates engine
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-12345"
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["LLM_MODEL"] = "gpt-3.5-turbo"

# Mock heavy dependencies that crash on Windows
sys.modules['chromadb'] = MagicMock()
sys.modules['langchain_chroma'] = MagicMock()
sys.modules['langchain_chroma.vectorstores'] = MagicMock()
sys.modules['onnxruntime'] = MagicMock()
sys.modules['ragas'] = MagicMock()
sys.modules['ragas.metrics'] = MagicMock()
sys.modules['ragas.llms'] = MagicMock()
sys.modules['ragas.embeddings'] = MagicMock()
sys.modules['datasets'] = MagicMock()
sys.modules['rank_bm25'] = MagicMock()