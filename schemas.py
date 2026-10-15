from pydantic import BaseModel
from datetime import datetime

class UserBase(BaseModel):
    username: str
    password: str

class userdetails(UserBase):
    id : int
    username  : str

    class Config:
        orm_mode = True

#####################################

class DocumentResponse(BaseModel):
    id : int
    filename : str
    upload_date : datetime
    owner_id : int

    class Config:
        orm_mode = True

#####################################

class Token(BaseModel):
    access_token : str
    token_type : str

#####################################

class QuestionRequest(BaseModel):
    question: str
    document_id : int

class AnswerResponse(BaseModel):
    question: str
    answer: str
    document: str

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

class EvaluationResultResponse(BaseModel):
    id: int
    question: str
    answer: str
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_precision: float | None = None
    context_recall: float | None = None
    evaluation_latency_seconds: float | None = None
    created_at: datetime


    class Config:
        from_attributes = True