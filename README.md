# 🤖 AI 면접관 에이전트 v2

> 이력서 기반 AI 면접관 Agent - RAG + CrewAI 멀티 에이전트

---

## 📌 프로젝트 개요

| 항목       | 내용                  |
| ---------- | --------------------- |
| 프로젝트명 | AI 면접관 에이전트 v2 |
| 유형       | 개인 프로젝트         |
| 기간       | 2026.06               |
| 역할       | 전체 설계 및 구현     |

---

## 🎯 기존 프로젝트에서 발전한 점

기존 [ai-interview-agent](https://github.com/kang-y-j/ai-interview-agent)는 LangChain + LangGraph 기반의 단일 파이프라인이었습니다.

이번 v2에서는 **CrewAI 멀티 에이전트**로 고도화했습니다.

|             | v1              | v2              |
| ----------- | --------------- | --------------- |
| 아키텍처    | 단일 파이프라인 | 멀티 에이전트   |
| 이력서 분석 | 직접 입력       | RAG 자동 검색   |
| UI          | 없음 (CLI)      | Streamlit 웹 UI |
| 에이전트 수 | 1개             | 면접관 + 평가자 |

---

## 🏗️ 시스템 아키텍처

```
이력서 PDF 업로드
      ↓
RAG로 이력서 내용 자동 검색 (FAISS + OpenAI Embeddings)
      ↓
면접관 에이전트 → 질문 3개 생성
      ↓
사용자 답변 입력
      ↓
평가자 에이전트 → 답변 평가 + 피드백
      ↓
Streamlit 웹 UI로 결과 출력
```

---

## 🛠️ 기술 스택

| 분류              | 기술                                |
| ----------------- | ----------------------------------- |
| **멀티 에이전트** | CrewAI                              |
| **RAG**           | LangChain, FAISS, OpenAI Embeddings |
| **LLM**           | OpenAI GPT-4o-mini                  |
| **웹 UI**         | Streamlit                           |
| **파일 처리**     | PyPDFLoader                         |

---

## 🚀 실행 방법

### 1. 패키지 설치

```bash
pip install langchain langchain-openai langchain-community langchain-text-splitters faiss-cpu pypdf crewai streamlit python-dotenv
```

### 2. 환경변수 설정

`.env` 파일 생성:

```
OPENAI_API_KEY=sk-...
```

### 3. 실행

```bash
streamlit run app.py
```

---

## 💡 주요 구현 포인트

- **RAG 자동 검색**: 이력서 PDF를 청크로 분할 후 벡터화하여 질문과 관련된 내용만 추출
- **CrewAI 멀티 에이전트**: 면접관 에이전트와 평가자 에이전트가 순차적으로 협업
- **chunk_size 최적화**: 300자로 설정하여 문맥 손실 없이 정확한 검색 가능

---

## 🔮 개선 아이디어

- [ ] 직무별 맞춤 질문 생성 (백엔드 / AI / 프론트엔드)
- [ ] 면접 결과 PDF 리포트 생성
- [ ] 음성 입력 지원 (STT 연동)
- [ ] Pinecone으로 벡터DB 교체 (대용량 처리)

---

## 👤 기여

| 이름   | 담당 역할                                                              |
| ------ | ---------------------------------------------------------------------- |
| 강영재 | 전체 설계 및 구현 (RAG 파이프라인, CrewAI 멀티 에이전트, Streamlit UI) |
