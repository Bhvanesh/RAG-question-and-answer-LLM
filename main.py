from database import Base, engine, SessionLocal
from dotenv import load_dotenv
import time
from models import User, Document, EvaluationResult
from evalutor import evaluate_rag_response
from schemas import DocumentResponse, UserBase, UserResponse, Token, QuestionRequest, AnswerResponse, EvaluationRequest, EvaluationScores, EvaluationResponse, EvaluationResultResponse
from auth import verify_token, create_token, verify_password, hash_password
from ai_engine import answer_question, process_document
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging
import os
from datetime import datetime
import uuid
from pathlib import Path
import json

##################Logging Configuration##################
logging.basicConfig(
level=logging.INFO,
format="%(asctime)s - %(levelname)s - %(message)s",
handlers=[logging.StreamHandler(), logging.FileHandler("app.log")])

oauth2_schema = OAuth2PasswordBearer(tokenUrl="login")

load_dotenv(override = False)

Base.metadata.create_all(bind = engine)
logger = logging.getLogger(__name__)
os.makedirs("./uploads", exist_ok=True)

app = FastAPI()
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
###################Middleware###########################
@app.middleware("http")
async def log_request(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request started | {request.method}")
    response = await call_next(request)
    endtime = (time.time() - start_time)*1000
    logger.info(f"Request completed | {request.method} and took {endtime:.2f} ms")
    return response
###################Exception Handling###########################
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error | {request.url} | {str(exc)}")
    return JSONResponse(status_code=500, content = {"status":"error", "message": "Internal Server Error"})

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def error_response(status_code: int, message: str):
    raise HTTPException(status_code=status_code, detail = {"status": "error", "message": message})

def authenticate_user(token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail={"status": "error", "message": "Invalid token"})
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail={"status": "401", "message": "User not found"})
    return user


################Authentication###########################

@app.post("/register", response_model = UserResponse)
async def register(user: UserBase, db : Session = Depends(get_db)):
    try:
        logger.info(f"Attempting to register user | {user.username}")
        existingUser = db.query(User).filter(User.username == user.username).first()
        if existingUser:
            logger.warning(f"Username already exists | {user.username}")
            error_response(status_code = 400, message = "Username already exists")
        new_user = User(
            username = user.username,
            password = hash_password(user.password) 
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User registered successfully | {new_user.username}")
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception occurred while registering user | {user.username} | {str(e)}")
        error_response(status_code = 500, message = f"Exception occured : {str(e)}")

@app.post("/login", response_model = Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        username = db.query(User).filter(User.username == form_data.username).first()
        if not username or not verify_password(form_data.password, username.password):
            error_response(status_code=401, message="Invalid username or password")
        access_token = create_token(data={"sub": username.username})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception occurred while logging in user | {form_data.username} | {str(e)}")
        error_response(status_code=500, message=f"Exception occured : {str(e)}")


##################User Endpoints##################

@app.post("/upload", response_model=DocumentResponse)
async def upload(file : UploadFile = File(...), db: Session = Depends(get_db), Currentuser: User = Depends(authenticate_user)):

    try:
        original_name = file.filename or "unnamed"
        ext = Path(original_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            error_response(status_code=400, message="Invalid file type. Only PDF and DOCX files are allowed.")
        
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            error_response(status_code=400, message="File size exceeds the maximum limit of 10 MB.")

        safe_filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join("./uploads", safe_filename)

        with open(filepath, "wb") as f:
            f.write(contents)
        logger.info(f"Document saved to {filepath} | {safe_filename}")

        document = Document(filename=file.filename, stored_filename=safe_filename, upload_date=datetime.utcnow(), owner_id=Currentuser.id)
        db.add(document)
        db.commit()
        db.refresh(document)
        logger.info(f"Document details saved to DB | {document.id}")

        process_document(filepath, document.id)
        logger.info(f"Document processed into chunks | {document.id}")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception occurred while uploading document | {file.filename} | {str(e)}")
        error_response(status_code=500, message=f"Internal server error")

@app.get("/documents", response_model=list[DocumentResponse])
async def get_documents(db: Session = Depends(get_db), Currentuser: User = Depends(authenticate_user)):
    try:
        existingdoc = db.query(Document).filter(Document.owner_id == Currentuser.id).all()
        if not existingdoc:
            error_response(status_code=404, message="No documents found")
        return existingdoc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception occurred while fetching documents for user | {Currentuser.username} | {str(e)}")
        error_response(status_code=500, message=f"Internal server error")


@app.post("/question", response_model=AnswerResponse)
async def ask_question(data: QuestionRequest, db: Session = Depends(get_db), Currentuser: User = Depends(authenticate_user)):
    try:
        logger.info(f"User | {Currentuser.username} | asked question | {data.question}")
        document = db.query(Document).filter(data.document_id == Document.id, Document.owner_id == Currentuser.id).first()
        if not document:
            error_response(status_code=404, message="Document not found")

        result = answer_question(document.id, data.question)
        answers = result["answer"]
       
        return { "question": data.question, "answer": answers, "document": document.filename}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception occurred while asking question for user | {Currentuser.username} | {str(e)}")
        error_response(status_code=500, message=f"Internal server error")


@app.post("/ask/evaluate", response_model = EvaluationResponse)
async def ask_with_evaluator(request: EvaluationRequest, db: Session = Depends(get_db), CurrentUser: User = Depends(authenticate_user)):
    try:
        logger.info(f"Evaluation request | {CurrentUser.username} | {request.question}")
        document = db.query(Document).filter(Document.id == request.document_id, Document.owner_id == CurrentUser.id).first()
        if not document:
            error_response(status_code=404, message="Document not found")

        result = answer_question(document.id, request.question)
        answers = result["answer"] 
        context = result["contexts"]
        logger.info(f"Running RAGAS evaluation for document | {document.filename}")
        scores = evaluate_rag_response( question = request.question, answer = answers, context = context, ground_truth = request.ground_truth)

        evaluation = EvaluationResult(
            document_id=request.document_id,
            question=request.question,
            answer=answers,
            context_precision=scores["context_precision"],
            context_recall=scores["context_recall"],
            faithfulness=scores["faithfulness"],
            answer_relevancy=scores["answer_relevancy"],
            evaluation_latency_seconds=scores["evaluation_latency_seconds"],
            created_at=datetime.utcnow()
        )
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)

        return {"question": request.question, "answer": answers, "document": document.filename, "evaluation_score": EvaluationScores(
        faithfulness=scores["faithfulness"], answer_relevancy=scores["answer_relevancy"], context_precision=scores["context_precision"],
        context_recall=scores["context_recall"], evaluation_latency_seconds=scores["evaluation_latency_seconds"])}
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Exception occurred while asking question for user | {CurrentUser.username} | {str(e)}")
        error_response(status_code=500, message=f"Internal server error")


@app.get("/evaluations", response_model=list[EvaluationResultResponse])
async def get_evaluations(
    db: Session = Depends(get_db),
    Currentuser: User = Depends(authenticate_user)
):
    try:
        evaluations = db.query(EvaluationResult).join(Document).filter(Document.owner_id == Currentuser.id).all()
        return evaluations
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Exception occurred while fetching evaluations for user | {Currentuser.username} | {str(e)}")
        error_response(status_code=500, message=f"Internal server error")



@app.post("/batch-evaluate")
async def batch_evaluate(db: Session = Depends(get_db),
                         Currentuser: User = Depends(authenticate_user)):
    try:
        with open("golden_dataset.json", "r") as f:
            data = json.load(f)

        document_id = data["document_id"]
        test_cases = data["test_cases"]

        # verify document belongs to user
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == Currentuser.id
        ).first()
        if not document:
            error_response(status_code=404, message="Document not found")

        results = []
        for case in test_cases:
            question = case["question"]
            ground_truth = case["ground_truth"]
            try:
                rag_result = answer_question(document_id, question)
                scores = evaluate_rag_response(
                    question=question,
                    answer=rag_result["answer"],
                    context=rag_result["contexts"],
                    ground_truth=ground_truth
                )
                results.append({
                    "question": question,
                    "faithfulness": scores["faithfulness"],
                    "answer_relevancy": scores["answer_relevancy"],
                    "context_precision": scores["context_precision"],
                    "context_recall": scores["context_recall"]
                })
            except Exception as e:
                logger.error(f"Batch eval failed for question | {question} | {str(e)}")
                results.append({"question": question, "error": str(e)})

        # aggregate
        def avg(metric):
            vals = [r[metric] for r in results
                    if metric in r and r[metric] is not None]
            return round(sum(vals) / len(vals), 3) if vals else None

        aggregate = {
            "avg_faithfulness": avg("faithfulness"),
            "avg_answer_relevancy": avg("answer_relevancy"),
            "avg_context_precision": avg("context_precision"),
            "avg_context_recall": avg("context_recall"),
            "total_questions": len(results),
            "failed": len([r for r in results if "error" in r])
        }

        return {"aggregate": aggregate, "detailed_results": results}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch evaluation error | {str(e)}")
        error_response(status_code=500, message="Batch evaluation failed")