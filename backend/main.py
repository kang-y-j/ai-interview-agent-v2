import os
import tempfile
from agents import generate_questions, evaluate_answer, generate_followup
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from rag import create_vectorstore, search_resume
from agents import generate_questions, evaluate_answer
from agents import generate_questions, evaluate_answer, generate_followup, generate_overall_feedback

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

vectorstores = {}

@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    
    vectorstore = create_vectorstore(tmp_path)
    session_id = os.path.basename(tmp_path)
    vectorstores[session_id] = vectorstore
    
    return {"session_id": session_id}

@app.post("/questions/{session_id}")
async def get_questions(session_id: str, data: dict):
    vectorstore = vectorstores[session_id]
    resume_content = search_resume(vectorstore, "스킬 프로젝트 경험 학력 자격증")
    
    job_field = data.get("job_field", "일반")
    level = data.get("level", "신입")
    
    questions_text = await generate_questions(resume_content, job_field, level)
    
    questions = []
    for line in questions_text.strip().split("\n"):
        line = line.strip()
        if line and line[0].isdigit():
            questions.append(line)
    
    return {"questions": questions}

@app.post("/evaluate")
async def evaluate(data: dict):
    question = data["question"]
    answer = data["answer"]
    job_field = data.get("job_field", "일반")
    level = data.get("level", "신입")
    feedback = await evaluate_answer(question, answer, job_field, level)
    return {"feedback": feedback}

@app.get("/")
def root():
    return {"message": "AI 면접관 API 작동 중!"}


@app.post("/followup")
async def followup(data: dict):
    question = data["question"]
    answer = data["answer"]
    previous_questions = data.get("previous_questions", [])
    job_field = data.get("job_field", "일반")
    level = data.get("level", "신입")
    
    result = await generate_followup(question, answer, previous_questions, job_field, level)
    
    if result.startswith("FOLLOWUP:"):
        followup_question = result.replace("FOLLOWUP:", "").strip()
        return {"has_followup": True, "question": followup_question}
    else:
        return {"has_followup": False, "question": None}
    
@app.post("/overall-feedback")
async def overall_feedback(data: dict):
    history = data["history"]
    job_field = data.get("job_field", "일반")
    level = data.get("level", "신입")
    feedback = await generate_overall_feedback(history, job_field, level)
    return {"feedback": feedback}