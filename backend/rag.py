import os
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader

def create_vectorstore(pdf_path: str):
    embeddings = OpenAIEmbeddings()
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )
    chunks = text_splitter.split_documents(documents)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore

def search_resume(vectorstore, query: str):
    docs = vectorstore.similarity_search(query, k=3)
    return "\n".join([doc.page_content for doc in docs])


def detect_language(text: str) -> str:
    """이력서 텍스트의 언어를 글자 비율로 감지한다(LLM 불필요).
    한글이 영문 알파벳보다 많으면 한국어, 아니면 영어로 본다."""
    hangul = sum(1 for c in text if "가" <= c <= "힣")
    latin = sum(1 for c in text if c.isascii() and c.isalpha())
    return "한국어" if hangul >= latin else "English"