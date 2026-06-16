"""
AI 면접관 에이전트 - Hugging Face Spaces 배포용 단일 Streamlit 앱.

원본 프로젝트는 FastAPI(백엔드) + Streamlit(프론트)로 분리돼 있지만,
HF Spaces는 앱 하나만 돌리므로 백엔드 함수(rag, agents)를 HTTP 없이
직접 import 해서 호출하도록 합쳤다.

필요한 환경변수(Space의 Secrets에 설정):
  - OPENAI_API_KEY : OpenAI API 키
"""
import os
import asyncio
import tempfile

import streamlit as st
from dotenv import load_dotenv

from rag import create_vectorstore, search_resume
from agents import (
    generate_questions,
    evaluate_answer,
    generate_followup,
    generate_overall_feedback,
)

load_dotenv()  # 로컬 실행 시 .env 사용 (HF에서는 Secrets가 환경변수로 주입됨)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB
PDF_MAGIC = b"%PDF-"


def run_async(coro):
    """Streamlit(동기 환경)에서 async 에이전트 함수를 호출하기 위한 헬퍼."""
    return asyncio.run(coro)


st.title("🤖 AI 면접관 에이전트")
st.write("이력서 기반으로 면접 질문을 생성하고 답변을 평가해줍니다.")

# OpenAI 키 미설정 시 안내
if not os.getenv("OPENAI_API_KEY"):
    st.error("⚠️ OPENAI_API_KEY 가 설정되지 않았습니다. (Space → Settings → Secrets 에서 설정하세요)")
    st.stop()

# 1. PDF 업로드
uploaded_file = st.file_uploader("이력서 PDF를 업로드하세요", type="pdf")

if uploaded_file:
    st.success("이력서 업로드 완료!")

    col1, col2 = st.columns(2)
    with col1:
        job_field = st.selectbox("직무 분야", [
            "AI/ML", "백엔드", "프론트엔드", "경영/기획",
            "시설/건축", "전기/전자", "마케팅", "데이터 분석", "기타"
        ])
    with col2:
        level = st.selectbox("지원자 수준", ["신입", "주니어 (1~3년)", "시니어 (3년 이상)"])

    if st.button("면접 시작"):
        # --- 업로드 검증 (원본 백엔드 /upload 로직과 동일) ---
        content = uploaded_file.getvalue()
        if len(content) == 0:
            st.error("빈 파일입니다.")
            st.stop()
        if len(content) > MAX_UPLOAD_BYTES:
            st.error("파일이 너무 큽니다. (최대 5MB)")
            st.stop()
        if not content.startswith(PDF_MAGIC):
            st.error("올바른 PDF 파일이 아닙니다.")
            st.stop()

        with st.spinner("이력서 분석 중..."):
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                vectorstore = create_vectorstore(tmp_path)
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)

            st.session_state.vectorstore = vectorstore
            st.session_state.job_field = job_field
            st.session_state.level = level

        with st.spinner("질문 생성 중..."):
            resume_content = search_resume(vectorstore, "스킬 프로젝트 경험 학력 자격증")
            questions_text = run_async(generate_questions(resume_content, job_field, level))

            questions = []
            for line in questions_text.strip().split("\n"):
                line = line.strip()
                if line and line[0].isdigit():
                    questions.append(line)

            st.session_state.questions = questions
            st.session_state.started = True
            st.session_state.current_q = 0
            st.session_state.followup_count = 0
            st.session_state.current_question = questions[0]
            st.session_state.history = []
            st.session_state.previous_questions = []
            st.session_state.interview_done = False

# 2. 면접 진행 UI
if "started" in st.session_state and st.session_state.started and not st.session_state.get("interview_done"):
    total = len(st.session_state.questions)
    current_q = st.session_state.current_q
    followup_count = st.session_state.followup_count

    st.progress((current_q) / total)
    st.caption(f"질문 {current_q + 1} / {total}")

    if followup_count > 0:
        st.caption(f"꼬리질문 {followup_count} / 2")

    st.subheader("📋 " + st.session_state.current_question)

    answer = st.text_area("답변을 입력하세요", key=f"answer_{current_q}_{followup_count}")

    if st.button("답변 제출"):
        if answer.strip():
            job_field = st.session_state.job_field
            level = st.session_state.level
            question = st.session_state.current_question

            st.session_state.history.append({
                "question": question,
                "answer": answer,
            })
            st.session_state.previous_questions.append(question)

            if followup_count < 2:
                with st.spinner("다음 질문 준비 중..."):
                    result = run_async(generate_followup(
                        question,
                        answer,
                        st.session_state.previous_questions,
                        job_field,
                        level,
                    ))
                    has_followup = result.startswith("FOLLOWUP:")
                    followup_question = result.replace("FOLLOWUP:", "").strip() if has_followup else None

                if has_followup:
                    st.session_state.current_question = followup_question
                    st.session_state.followup_count += 1
                    st.rerun()
                else:
                    next_q = current_q + 1
                    if next_q < total:
                        st.session_state.current_q = next_q
                        st.session_state.followup_count = 0
                        st.session_state.current_question = st.session_state.questions[next_q]
                        st.rerun()
                    else:
                        st.session_state.interview_done = True
                        st.rerun()
            else:
                next_q = current_q + 1
                if next_q < total:
                    st.session_state.current_q = next_q
                    st.session_state.followup_count = 0
                    st.session_state.current_question = st.session_state.questions[next_q]
                    st.rerun()
                else:
                    st.session_state.interview_done = True
                    st.rerun()

# 3. 면접 완료 & 평가
if "interview_done" in st.session_state and st.session_state.interview_done:
    st.success("🎉 면접이 완료되었습니다!")

    # 개별 평가
    st.header("📊 질문별 상세 피드백")
    for i, item in enumerate(st.session_state.history):
        with st.spinner(f"질문 {i+1} 평가 중..."):
            feedback = run_async(evaluate_answer(
                item["question"],
                item["answer"],
                st.session_state.job_field,
                st.session_state.level,
            ))

        with st.expander(f"질문 {i+1}: {item['question'][:40]}..."):
            st.write(f"**Q: {item['question']}**")
            st.write(f"A: {item['answer']}")
            st.divider()
            st.write(feedback)

    # 종합 피드백
    st.header("🎯 종합 피드백")
    with st.spinner("종합 피드백 생성 중..."):
        overall = run_async(generate_overall_feedback(
            st.session_state.history,
            st.session_state.job_field,
            st.session_state.level,
        ))
    st.write(overall)
