from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

OPENAI_API_KEY = "여기에_API_키_입력"

# 1. LLM 설정
llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)

# 2. 임베딩 설정
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# 3. PDF 불러오기
loader = PyPDFLoader(r"E:\crewai\resume.pdf")
documents = loader.load()

# 4. 청크로 자르기
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50
)
chunks = text_splitter.split_documents(documents)

# 5. 벡터DB에 저장
vectorstore = FAISS.from_documents(chunks, embeddings)

# 6. 프롬프트 설정
prompt = ChatPromptTemplate.from_template("""
아래 context를 참고해서 질문에 답해줘.

context: {context}

질문: {question}
""")

# 7. RAG 체인 구성
chain = (
    {"context": vectorstore.as_retriever(), "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 8. 질문하기
result = chain.invoke("이 사람의 주요 스킬이 뭐야?")
print(result)