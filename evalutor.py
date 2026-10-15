from dotenv import load_dotenv
import time
import os
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas import evaluate
from ragas.metrics import (faithfulness, answer_relevancy, context_precision, context_recall)
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from datasets import Dataset

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def evaluate_rag_response(question: str, answer: str, context: list[str], ground_truth:str = None):
    
    if isinstance(context, str):
        context = [context]
    if not context:
        context = ["No context available"]


    """ Evaluate a RAG response using RAGAS metrics.
    question -> what the user asked
    answer -> what the AI answered
    contexts -> the chunks retrived from ChromaDB
    ground_truth -> optional correct answer for comparison"""

    #data = {"question":[question], "answer":[answer], "contexts": [context]}
    data = {
        "user_input": [question],
        "response": [answer],
        "retrieved_contexts": [context]
    }
    if ground_truth:
        data["ground_truth"] = [ground_truth]

    dataset = Dataset.from_dict(data)

    llm = ChatOpenAI(
        model = "gpt-3.5-turbo",
        openai_api_key = OPENAI_API_KEY,
        temperature = 0
    )

    embeddings = OpenAIEmbeddings(openai_api_key = OPENAI_API_KEY)

    wrapped_llm = LangchainLLMWrapper(llm)
    wrapped_embeddings = LangchainEmbeddingsWrapper(embeddings)

    metrics = [faithfulness, answer_relevancy, context_precision]

    if ground_truth:
        metrics.append(context_recall)
    
    start_time = time.time()
    results = evaluate(
        dataset = dataset,
        metrics = metrics,
        llm = wrapped_llm,
        embeddings = wrapped_embeddings
    )

    latency = round(time.time() - start_time, 2)

    scores = results.to_pandas().to_dict(orient="records")[0]

    return{

        "faithfulness" : round(float(scores.get("faithfulness", 0)),3),
        "answer_relevancy" : round(float(scores.get("answer_relevancy", 0)),3),
        "context_precision" : round(float(scores.get("context_precision", 0)),3),
        "context_recall" : round(float(scores.get("context_recall", 0)),3),
        "evaluation_latency_seconds": latency
    }