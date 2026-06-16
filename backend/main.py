import os
import secrets
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from rag import create_vectorstore, search_resume
from agents import (
    generate_questions,
    evaluate_answer,
    generate_followup,
    generate_overall_feedback,
)

load_dotenv()

app = FastAPI()

# 허용할 프론트엔드 origin 을 환경변수(ALLOWED_ORIGINS, 콤마 구분)로 제한.
# 미설정 시 로컬 Streamlit 기본 주소만 허용한다.
_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501")
ALLOWED_ORIGINS = [o.strip() for o in _origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 업로드 제한
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB
PDF_MAGIC = b"%PDF-"

vectorstores = {}


# ---- 요청 본문 스키마 (검증) ----
class QuestionsRequest(BaseModel):
    job_field: str = "일반"
    level: str = "신입"


class EvaluateRequest(BaseModel):
    question: str
    answer: str
    job_field: str = "일반"
    level: str = "신입"


class FollowupRequest(BaseModel):
    question: str
    answer: str
    previous_questions: list[str] = Field(default_factory=list)
    job_field: str = "일반"
    level: str = "신입"


class HistoryItem(BaseModel):
    question: str
    answer: str


class OverallFeedbackRequest(BaseModel):
    history: list[HistoryItem]
    job_field: str = "일반"
    level: str = "신입"


@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    content = await file.read()

    # 크기 검증
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="파일이 너무 큽니다. (최대 5MB)")

    # 실제 PDF 인지 매직바이트로 검증 (content-type 헤더는 위조 가능)
    if not content.startswith(PDF_MAGIC):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드할 수 있습니다.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        vectorstore = create_vectorstore(tmp_path)
    finally:
        # 임시 파일은 벡터스토어 생성 후 즉시 삭제 (디스크 누적 방지)
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    # 추측 불가능한 세션 ID 발급 (임시파일명 기반 IDOR 방지)
    session_id = secrets.token_urlsafe(24)
    vectorstores[session_id] = vectorstore

    return {"session_id": session_id}


def _get_vectorstore(session_id: str):
    vectorstore = vectorstores.get(session_id)
    if vectorstore is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return vectorstore


@app.post("/questions/{session_id}")
async def get_questions(session_id: str, data: QuestionsRequest):
    vectorstore = _get_vectorstore(session_id)
    resume_content = search_resume(vectorstore, "스킬 프로젝트 경험 학력 자격증")

    questions_text = await generate_questions(
        resume_content, data.job_field, data.level
    )

    questions = []
    for line in questions_text.strip().split("\n"):
        line = line.strip()
        if line and line[0].isdigit():
            questions.append(line)

    return {"questions": questions}


@app.post("/evaluate")
async def evaluate(data: EvaluateRequest):
    feedback = await evaluate_answer(
        data.question, data.answer, data.job_field, data.level
    )
    return {"feedback": feedback}


@app.get("/")
def root():
    return {"message": "AI 면접관 API 작동 중!"}


@app.post("/followup")
async def followup(data: FollowupRequest):
    result = await generate_followup(
        data.question,
        data.answer,
        data.previous_questions,
        data.job_field,
        data.level,
    )

    if result.startswith("FOLLOWUP:"):
        followup_question = result.replace("FOLLOWUP:", "").strip()
        return {"has_followup": True, "question": followup_question}
    else:
        return {"has_followup": False, "question": None}


@app.post("/overall-feedback")
async def overall_feedback(data: OverallFeedbackRequest):
    history = [item.model_dump() for item in data.history]
    feedback = await generate_overall_feedback(history, data.job_field, data.level)
    return {"feedback": feedback}
