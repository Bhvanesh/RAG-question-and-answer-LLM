from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)

class UserResponse(BaseModel):
    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)

#####################################

class DocumentResponse(BaseModel):
    id : int
    filename : str
    upload_date : datetime
    owner_id : int
    model_config = ConfigDict(from_attributes=True)

#####################################

class Token(BaseModel):
    access_token : str
    token_type : str

#####################################

class QuestionRequest(BaseModel):
    question: str
    document_id : int

class SourceChunk(BaseModel):
    content: str
    page: int | None = None

class AnswerResponse(BaseModel):
    question: str
    answer: str
    document: str
    sources: list[SourceChunk] = []    

class EvaluationRequest(BaseModel):
    document_id: int
    question: str
    ground_truth: str | None = None 

class EvaluationScores(BaseModel):
    faithfulness: float| None = None
    answer_relevancy: float| None = None
    context_precision: float| None = None
    context_recall: float| None = None
    evaluation_latency_seconds: float| None = None

class EvaluationResponse(BaseModel):
    question: str
    answer: str
    document: str
    evaluation_score: EvaluationScores
    sources: list[SourceChunk] = []


class EvaluationResultResponse(BaseModel):
    id: int
    document_id: int          
    question: str
    answer: str
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_precision: float | None = None
    context_recall: float | None = None
    evaluation_latency_seconds: float | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)