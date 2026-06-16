import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

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
            res = requests.post(f"{API_URL}/upload", files=files)
            session_id = res.json()["session_id"]
            st.session_state.session_id = session_id
            st.session_state.job_field = job_field
            st.session_state.level = level

        with st.spinner("질문 생성 중..."):
            res = requests.post(f"{API_URL}/questions/{session_id}", json={
                "job_field": job_field,
                "level": level
            })
            st.session_state.questions = res.json()["questions"]
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
                    res = requests.post(f"{API_URL}/followup", json={
                        "question": question,
                        "answer": answer,
                        "previous_questions": st.session_state.previous_questions,
                        "job_field": job_field,
                        "level": level
                    })
                    data = res.json()

                if data["has_followup"]:
                    st.session_state.current_question = data["question"]
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
            res = requests.post(f"{API_URL}/evaluate", json={
                "question": item["question"],
                "answer": item["answer"],
                "job_field": st.session_state.job_field,
                "level": st.session_state.level
            })
            feedback = res.json()["feedback"]

        with st.expander(f"질문 {i+1}: {item['question'][:40]}..."):
            st.write(f"**Q: {item['question']}**")
            st.write(f"A: {item['answer']}")
            st.divider()
            st.write(feedback)

    # 종합 피드백
    st.header("🎯 종합 피드백")
    with st.spinner("종합 피드백 생성 중..."):
        res = requests.post(f"{API_URL}/overall-feedback", json={
            "history": st.session_state.history,
            "job_field": st.session_state.job_field,
            "level": st.session_state.level
        })
        overall = res.json()["feedback"]
    st.write(overall)