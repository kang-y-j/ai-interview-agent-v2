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
        chunk_overlap=50,
    )
    chunks = text_splitter.split_documents(documents)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore


def search_resume(vectorstore, query: str):
    docs = vectorstore.similarity_search(query, k=3)
    return "\n".join([doc.page_content for doc in docs])
