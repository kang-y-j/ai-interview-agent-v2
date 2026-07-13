import os
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT_SECONDS = 90

# 백엔드와 공유하는 비밀 키. 환경변수 APP_API_KEY 로 설정한다.
# (백엔드에서 키를 설정하지 않았다면 빈 값이어도 동작한다)
API_KEY = os.getenv("APP_API_KEY", "")
HEADERS = {"X-API-Key": API_KEY} if API_KEY else {}


def post_api(path, **kwargs):
    try:
        response = requests.post(
            f"{API_URL}{path}",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT_SECONDS,
            **kwargs,
        )
    except requests.RequestException:
        st.error("백엔드에 연결하지 못했습니다. 잠시 후 다시 시도하세요.")
        return None

    try:
        payload = response.json()
    except ValueError:
        st.error("백엔드가 올바르지 않은 응답을 반환했습니다. 잠시 후 다시 시도하세요.")
        return None

    if not response.ok:
        detail = payload.get("detail") if isinstance(payload, dict) else None
        st.error(detail or "요청을 처리하지 못했습니다. 잠시 후 다시 시도하세요.")
        return None

    if not isinstance(payload, dict):
        st.error("백엔드 응답 형식이 올바르지 않습니다. 잠시 후 다시 시도하세요.")
        return None

    return payload

st.title("🤖 AI 면접관 에이전트")
st.write("이력서 기반으로 면접 질문을 생성하고 답변을 평가해줍니다.")

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
        with st.spinner("이력서 분석 중..."):
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            upload_result = post_api("/upload", files=files)
            if upload_result is None or not upload_result.get("session_id"):
                st.stop()
            session_id = upload_result["session_id"]
            st.session_state.session_id = session_id
            st.session_state.job_field = job_field
            st.session_state.level = level

        with st.spinner("질문 생성 중..."):
            questions_result = post_api(f"/questions/{session_id}", json={
                "job_field": job_field,
                "level": level
            })
            if questions_result is None:
                st.stop()
            questions = questions_result.get("questions")
            if not isinstance(questions, list) or not questions:
                st.error("생성된 질문이 없습니다. 다시 시도하세요.")
                st.stop()
            st.session_state.questions = questions
            # 백엔드가 이력서 언어를 감지해 알려준다 → 면접 전체를 그 언어로 진행
            st.session_state.language = questions_result.get("language", "한국어")
            st.session_state.started = True
            st.session_state.current_q = 0
            st.session_state.followup_count = 0
            st.session_state.current_question = st.session_state.questions[0]
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
                "answer": answer
            })
            st.session_state.previous_questions.append(question)

            if followup_count < 2:
                with st.spinner("다음 질문 준비 중..."):
                    followup_result = post_api("/followup", json={
                        "question": question,
                        "answer": answer,
                        "previous_questions": st.session_state.previous_questions,
                        "job_field": job_field,
                        "level": level,
                        "language": st.session_state.language
                    })
                    if followup_result is None:
                        st.stop()

                # 꼬리질문이 이미 물어본 질문과 같으면(모델이 원질문을 복제하는 경우) 스킵
                followup_q = followup_result["question"] if followup_result.get("has_followup") else None
                asked = {q.strip() for q in st.session_state.previous_questions}
                is_new_followup = bool(followup_q) and followup_q.strip() not in asked

                if is_new_followup:
                    st.session_state.current_question = followup_q
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
            evaluation_result = post_api("/evaluate", json={
                "question": item["question"],
                "answer": item["answer"],
                "job_field": st.session_state.job_field,
                "level": st.session_state.level,
                "language": st.session_state.language
            })
            if evaluation_result is None:
                continue
            feedback = evaluation_result.get("feedback")
            if not isinstance(feedback, str):
                st.error("평가 결과 형식이 올바르지 않습니다. 잠시 후 다시 시도하세요.")
                continue

        with st.expander(f"질문 {i+1}: {item['question'][:40]}..."):
            st.write(f"**Q: {item['question']}**")
            st.write(f"A: {item['answer']}")
            st.divider()
            st.write(feedback)

    # 종합 피드백
    st.header("🎯 종합 피드백")
    with st.spinner("종합 피드백 생성 중..."):
        overall_result = post_api("/overall-feedback", json={
            "history": st.session_state.history,
            "job_field": st.session_state.job_field,
            "level": st.session_state.level,
            "language": st.session_state.language
        })
        if overall_result is None:
            st.stop()
        overall = overall_result.get("feedback")
        if not isinstance(overall, str):
            st.error("종합 피드백 형식이 올바르지 않습니다. 잠시 후 다시 시도하세요.")
            st.stop()
    st.write(overall)
