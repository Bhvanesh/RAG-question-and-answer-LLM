from sqlalchemy import Column, DateTime, Integer, Float, String, ForeignKey
from database import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    documents = relationship("Document", back_populates="owner")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="documents")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    question = Column(String, nullable=False)
    answer = Column(String, nullable =False)
    context_precision = Column(Float, nullable=False)
    context_recall = Column(Float, nullable=False)
    faithfulness = Column(Float, nullable=False)
    answer_relevancy = Column(Float, nullable=False)
    evaluation_latency_seconds = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

