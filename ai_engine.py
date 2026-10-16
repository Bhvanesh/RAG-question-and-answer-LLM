from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
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

    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model = LLM_MODEL, temperature=0)
    #qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
    answer = retriever.invoke(question)


    context = [doc.page_content for doc in answer]
    sources = [ {"content": doc.page_content, "page": doc.metadeta.get("page")} for doc in docs]
    context_text = "\n\n".join(context)
    prompt = f"""You are a helpful assistant analyzing a document. Answer the question clearly and professionally.Format your response in a clean, readable way.
    If listing items, number them properly. If the information is not in the document, say so clearly. Context: {context_text} Question: {question} Answer:"""
    response = llm.invoke(prompt)
    answers = response.content
    return { "answer": answers, "contexts": context, "sources": sources }

