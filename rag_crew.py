import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from crewai import Agent, Task, Crew, LLM

load_dotenv()

# 1. RAG 설정
embeddings = OpenAIEmbeddings()
loader = PyPDFLoader(r"C:\Users\kfccc\OneDrive\Desktop\crewai\resume.pdf")
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50
)
chunks = text_splitter.split_documents(documents)
vectorstore = FAISS.from_documents(chunks, embeddings)

# 2. 이력서 검색
def search_resume(query):
    docs = vectorstore.similarity_search(query, k=3)
    return "\n".join([doc.page_content for doc in docs])

resume_content = search_resume("스킬 프로젝트 경험 학력 자격증")

# 3. LLM 설정
llm = LLM(model="gpt-4o-mini")

# 4. 에이전트 정의
interviewer = Agent(
    role="interviewer",
    goal="Create sharp interview questions based on the resume",
    backstory="You are a professional AI developer interviewer.",
    llm=llm,
    verbose=False
)

evaluator = Agent(
    role="evaluator",
    goal="Evaluate the applicant's answer and give detailed feedback in Korean",
    backstory="You are an expert hiring consultant who evaluates interview answers fairly.",
    llm=llm,
    verbose=False
)

# 5. 질문 3개 생성
task1 = Task(
    description=f"""아래 이력서 내용을 보고 면접 질문 3개를 한국어로 만들어줘.
번호를 붙여서 질문만 출력하고 다른 설명은 하지마.

이력서 내용:
{resume_content}
""",
    expected_output="번호가 붙은 면접 질문 3개",
    agent=interviewer
)

crew1 = Crew(agents=[interviewer], tasks=[task1], verbose=False)
result1 = crew1.kickoff()
questions_text = str(result1)

# 6. 질문 파싱
questions = []
for line in questions_text.strip().split("\n"):
    line = line.strip()
    if line and (line[0].isdigit() or line.startswith("-")):
        questions.append(line)

print("\n" + "="*50)
print("🎤 면접 질문 목록:")
for q in questions:
    print(q)
print("="*50)

# 7. 질문별 답변 입력 + 평가
for i, question in enumerate(questions):
    print(f"\n📌 질문 {i+1}: {question}")
    answer = input("✍️  답변을 입력하세요: ")

    task_eval = Task(
        description=f"""아래 면접 질문과 지원자의 답변을 평가해줘. 한국어로 답해줘.

면접 질문: {question}
지원자 답변: {answer}

평가 항목:
1. 답변의 구체성 (1-5점)
2. 기술적 이해도 (1-5점)
3. 개선할 점
4. 잘한 점
""",
        expected_output="답변 평가 및 피드백",
        agent=evaluator
    )

    crew_eval = Crew(agents=[evaluator], tasks=[task_eval], verbose=False)
    result_eval = crew_eval.kickoff()

    print("\n📊 평가 결과:")
    print(result_eval)
    print("="*50)

print("\n✅ 면접 종료!")