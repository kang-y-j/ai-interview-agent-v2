# 🤖 AI 면접관 에이전트 v2

> 이력서(PDF)를 올리면 AI가 **맞춤 면접 질문을 생성 → 답변 평가 → 꼬리질문 → 종합 피드백**까지 해주는 RAG 기반 멀티 에이전트 서비스

<p align="left">
  <a href="https://kfccckyj-ai-interview-agent.hf.space">
    <img src="https://img.shields.io/badge/🚀_Live_Demo-바로_체험하기-FF4B4B?style=for-the-badge" alt="Live Demo">
  </a>
</p>

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-orange)
![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C)
![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o--mini-412991?logo=openai&logoColor=white)
![HuggingFace](https://img.shields.io/badge/🤗_Deployed-Hugging_Face_Spaces-FFD21E)

---

## 🔗 링크

| | |
| --- | --- |
| 🚀 **라이브 데모** | https://kfccckyj-ai-interview-agent.hf.space |
| 💻 **소스 코드** | https://github.com/kang-y-j/ai-interview-agent-v2 |

> 설치 없이 브라우저에서 바로 체험할 수 있습니다. (이력서 PDF만 준비하세요)

---

## 📸 데모

<!-- TODO: docs/screenshot.png 에 앱 실행 스크린샷을 넣으세요 (아래 줄 주석 해제) -->
<!-- ![데모 스크린샷](docs/screenshot.png) -->

> 이력서 업로드 → 직무/수준 선택 → 면접 시작 → AI가 이력서 기반 맞춤 질문 생성 → 답변 제출 → 꼬리질문 → 종합 피드백

---

## 📌 프로젝트 개요

| 항목 | 내용 |
| --- | --- |
| 프로젝트명 | AI 면접관 에이전트 v2 |
| 유형 | 개인 프로젝트 |
| 기간 | 2026.06 |
| 역할 | 전체 설계·구현·보안·배포 |
| 배포 | Hugging Face Spaces (라이브 운영 중) |

---

## ✨ 핵심 기능

- **이력서 기반 맞춤 질문 (RAG)** — PDF를 벡터화해 관련 내용을 검색하고, 그에 맞는 면접 질문을 생성
- **직무·난이도 맞춤** — 직무 분야(AI/ML·백엔드·프론트엔드 등)와 지원자 수준(신입·주니어·시니어)에 따라 질문/평가 난이도 조정
- **자동 꼬리질문** — 답변이 추상적이면 AI가 스스로 판단해 꼬리질문(최대 2회), 중복 주제나 "모르겠다"면 스킵
- **면접 코칭 평가** — 잘한 점 / 아쉬운 점 / 더 좋은 답변 예시 / 항목별 점수(구체성·직무이해도·전달력)
- **종합 피드백** — 전체 면접 총평 + 강점 + 개선점 + 준비 방법 + 최종 점수·합격 가능성

---

## 🏗️ 시스템 아키텍처

```
                  ┌────────────────────────┐
                  │   Streamlit (프론트)    │   사용자 UI
                  └───────────┬────────────┘
                              │ HTTP (JSON)
                              ▼
                  ┌────────────────────────┐
                  │    FastAPI (백엔드)     │   API 엔드포인트
                  │  /upload /questions     │
                  │  /evaluate /followup    │
                  │  /overall-feedback      │
                  └─────┬──────────────┬────┘
                        │              │
              ┌─────────▼───┐   ┌──────▼─────────┐
              │  RAG (rag)  │   │ Agents (agents)│
              │ PyPDF →     │   │  CrewAI 에이전트│
              │ 청크 분할 → │   │  면접관 / 코치  │
              │ 임베딩 →    │   └──────┬─────────┘
              │ FAISS 검색  │          │
              └─────────────┘          ▼
                                  ┌─────────┐
                                  │ OpenAI  │  gpt-4o-mini
                                  └─────────┘

배포: Hugging Face Spaces (단일 Streamlit 앱으로 통합 — 아래 '배포' 참고)
```

---

## 🛠️ 기술 스택

| 분류 | 기술 |
| --- | --- |
| **백엔드** | FastAPI, Pydantic, Uvicorn |
| **프론트엔드** | Streamlit |
| **멀티 에이전트** | CrewAI (면접관 / 평가 코치) |
| **RAG** | LangChain, FAISS, OpenAI Embeddings |
| **LLM** | OpenAI gpt-4o-mini |
| **파일 처리** | PyPDF |
| **배포** | Hugging Face Spaces |

---

## 🔒 보안 (Security)

> 단순 동작뿐 아니라 "배포해도 안전한가"를 기준으로 점검·보완했습니다.

| 영역 | 적용한 조치 |
| --- | --- |
| **비밀 관리** | API 키를 코드가 아닌 환경변수(`.env` / 배포 Secrets)로 분리. git 히스토리에 포함됐던 개인정보(이력서 PDF) 발견 후 레포 재구성 |
| **입력 검증** | 모든 요청 본문을 Pydantic 모델로 검증, 잘못된 입력은 422/404로 안전 처리 |
| **파일 업로드** | 크기 제한(5MB) + 매직바이트(`%PDF-`)로 실제 PDF 검증(헤더 위조 방지), 임시 파일 즉시 삭제 |
| **세션 보안** | 세션 ID를 `secrets.token_urlsafe`로 추측 불가능하게 발급 (IDOR 방지) |
| **인증** | API 키 헤더(`X-API-Key`) 인증, 타이밍 공격 방지를 위해 `hmac.compare_digest` 사용 |
| **CORS** | 와일드카드 제거, 허용 출처를 환경변수로 제한 |
| **프롬프트 인젝션** | 사용자 입력(이력서·답변)을 구분자로 감싸 "데이터로만" 취급하도록 시스템 지시 |

---

## 📂 프로젝트 구조

```
ai-interview-agent-v2/
├── backend/
│   ├── main.py        # FastAPI 엔드포인트 (인증·검증 포함)
│   ├── rag.py         # RAG 파이프라인 (PDF → 벡터스토어 → 검색)
│   └── agents.py      # CrewAI 에이전트 (질문/평가/꼬리질문/종합)
├── frontend/
│   └── app.py         # Streamlit UI
├── huggingface/       # HF Spaces 배포용 (단일 앱으로 통합한 버전)
│   ├── app.py
│   ├── agents.py
│   ├── rag.py
│   ├── requirements.txt
│   └── README.md
├── requirements.txt   # 로컬/백엔드 의존성
└── .env               # OPENAI_API_KEY 등 (git 미추적)
```

---

## 🚀 로컬 실행 방법

### 1. 설치
```bash
git clone https://github.com/kang-y-j/ai-interview-agent-v2.git
cd ai-interview-agent-v2
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 환경변수 (`.env` 생성)
```
OPENAI_API_KEY=sk-...
# (선택) 배포 시 API 보호용
APP_API_KEY=원하는_무작위_키
```

### 3. 실행 (터미널 2개)
```bash
# 터미널 1 — 백엔드
cd backend
uvicorn main:app --reload --port 8000

# 터미널 2 — 프론트엔드
streamlit run frontend/app.py
```

---

## ☁️ 배포 (Hugging Face Spaces)

원래 구조는 **FastAPI 백엔드 + Streamlit 프론트(2개 서비스)** 이지만,
HF Spaces는 Space 하나당 앱 하나만 실행합니다.

→ 프론트엔드가 백엔드 함수를 **HTTP 대신 직접 import 호출**하도록 통합한
버전(`huggingface/`)을 배포했습니다. (HTTP·CORS·포트 불필요 → 단순·안정)

GitHub 레포에는 본래의 분리 아키텍처를 그대로 유지해 설계 의도를 보존했습니다.

> 배포 시 필요한 Secret: `OPENAI_API_KEY`

---

## 🧩 트러블슈팅 / 배운 점

- **단일 앱 제약 → 아키텍처 통합 결정**: HF Spaces가 앱 하나만 지원해, 2개
  서비스를 합치되 본 구조는 레포에 보존하는 절충안을 택함.
- **async 함수를 Streamlit에서 호출**: 에이전트가 `kickoff_async`(비동기)라
  동기 환경인 Streamlit에서 `asyncio.run`으로 감싸 호출.
- **무거운 AI 의존성 배포**: crewai·faiss 등 무거운 패키지를 무료로 감당하기 위해
  자원이 넉넉한 HF Spaces(무료 16GB RAM)를 선택.
- **보안은 환경에 맞게**: 백엔드 버전은 API 키 인증으로, 공개 데모는 선불
  크레딧 캡으로 비용 위험을 통제 — 노출면에 따라 다른 방식 적용.

---

## 🔮 향후 개선

- [ ] 면접 결과 PDF 리포트 생성
- [ ] 음성 입력 지원 (STT 연동)
- [ ] 벡터스토어 영속화(DB/Redis) + 세션 만료(TTL)
- [ ] 상위 모델(gpt-4o) 옵션 + 평가 품질/비용 비교
- [ ] rate limiting + 인증을 갖춘 FastAPI 백엔드 별도 배포(2-서비스 라이브)

---

## 👤 만든 사람

| 이름 | 담당 |
| --- | --- |
| 강영재 | 전체 설계·구현 (RAG, CrewAI 멀티 에이전트, FastAPI/Streamlit), 보안 점검·보완, Hugging Face Spaces 배포 |
