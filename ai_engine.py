from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

##PROCESS and Load document

def process_document(file_path: str, document_id: int):
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
        pages = loader.load()
    elif file_path.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
        pages = loader.load()
    else:
        raise ValueError("Unsupported file format")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    chunks = splitter.split_documents(pages)

    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    vectorstore = Chroma.from_documents(documents = chunks, embedding= embeddings, persist_directory= f"./chroma_db/{document_id}")
    return len(chunks)

def answer_question(document_id: int, question:str):
    
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vectorstore = Chroma(persist_directory=f"./chroma_db/{document_id}", embedding_function=embeddings)

    retriever = vectorstore.as_retriever(search_kwargs={"k": 10}) # wrapping the vector store in the retiver obj and saying, retrive the top 10 most relevent question for the coming question

    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model = LLM_MODEL, temperature=0)
    #qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
    vector_docs = retriever.invoke(question)


    all_results = vectorstore.get()
    all_texts = all_results["documents"]
    all_metadata = all_results["metadatas"]

    tokenized_corpus = [text.lower().split() for text in all_texts]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_question = question.lower().split()
    bm25_scores = bm25.get_scores(tokenized_question)
    scored_chunks = sorted(zip(bm25_scores, all_texts, all_metadata),
    key=lambda x:x[0],
    reverse=True)[:10]

    bm25_docs = [Document(page_content=text, metadata=meta)
              for score, text, meta in scored_chunks if score > 0]

    combined_docs = reciprocal_rank_fusion(vector_docs, bm25_docs)
    final_docs = combined_docs[:3]
    context = [doc.page_content for doc in final_docs]
    sources = [{"content":doc.page_content, "page": doc.metadata.get("page")}for doc in final_docs]
    context_text = "\n\n".join(context)

    prompt = f"""You are a helpful assistant analyzing a document. Answer the question clearly and professionally.Format your response in a clean, readable way.
    If listing items, number them properly. If the information is not in the document, say so clearly. Context: {context_text} Question: {question} Answer:"""
    response = llm.invoke(prompt)
    answers = response.content
    return { "answer": answers, "contexts": context, "sources": sources }

def reciprocal_rank_fusion(vector_docs, bm25_docs, k=60):
        """
    Combines two ranked lists using Reciprocal Rank Fusion.
    vector_docs -> Documents from ChromaDB semantic search
    bm25_docs   -> Documents from BM25 keyword search
    k           -> smoothing constant (standard value 60)
    """
        scores = {}

        for rank, doc in enumerate(vector_docs):
             key = doc.page_content
             if key not in scores:
                  scores[key] = {"doc": doc, "score": 0}
             scores[key]["score"] += 1/ (rank + 1 +k)
             #scores[key]["score"] = scores[key]["score"] + 1 / (rank + 1 + k)

        for rank, doc in enumerate(bm25_docs):
             key  = doc.page_content
             if key not in scores:
                  scores[key] = {"doc": doc, "score": 0}
             scores[key]["score"]+= 1/(rank + 1 + k)
        
        sorted_results = sorted(scores.values(), key = lambda x: x["score"],
        reverse=True)

        return [item['doc'] for item in sorted_results]     
        
          
                  


