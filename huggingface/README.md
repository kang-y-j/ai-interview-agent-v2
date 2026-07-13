---
title: AI 면접관 에이전트
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.58.0
app_file: app.py
pinned: false
---

# 🤖 AI 면접관 에이전트

이력서(PDF)를 업로드하면 AI가 면접 질문을 생성하고, 답변을 평가하고,
꼬리질문을 던지며, 마지막에 종합 피드백을 제공합니다.

## 기술 스택
- **Streamlit** — UI
- **CrewAI** — 면접관/코치 AI 에이전트
- **LangChain + FAISS** — 이력서 RAG (검색 증강 생성)
- **OpenAI (gpt-5-mini)** — LLM

## 사용 방법
1. 이력서 PDF 업로드
2. 직무 분야 / 지원자 수준 선택
3. "면접 시작" → 질문에 답변 → 꼬리질문 → 종합 피드백

## 설정 (Secrets)
이 Space의 **Settings → Variables and secrets** 에 다음을 추가하세요:
- `OPENAI_API_KEY` : OpenAI API 키

## 아키텍처 참고
원본 프로젝트는 **FastAPI(백엔드) + Streamlit(프론트)** 로 분리 설계되어 있습니다.
([GitHub 저장소](https://github.com/kang-y-j/ai-interview-agent-v2))
이 Space에서는 단일 앱 환경에 맞춰 백엔드 함수를 직접 호출하도록 통합했습니다.
