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

