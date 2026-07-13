"""
면접 질문 생성 품질 평가 (LLM-as-a-judge)

목적: 프롬프트/모델 변경이 질문 품질을 실제로 개선했는지 정량 측정한다.
방법:
  - 4개 버전(V0 원본 → V1 모델 교체 → V2 프롬프트 → V3 단일주제 강제)으로
    같은 이력서들에 대해 질문을 생성한다.
  - 생성과 '다른' 모델(gpt-4o)을 심사관으로 써서 4개 지표를 0/1로 채점한다.
    (자기평가 편향 방지)
  - 버전별 지표 통과율(%)을 표로 출력하고 eval/results.md 에 저장한다.

실행: python eval/eval_questions.py
필요: .env 의 OPENAI_API_KEY
"""
import os
import json
import re
from collections import defaultdict

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

GEN_MODEL = "gpt-5-mini"      # 질문 생성 (실제 앱과 동일)
JUDGE_MODEL = "gpt-4o"   # 심사관 (생성과 다른 모델 → 편향 완화)

# ---------------------------------------------------------------------------
# 평가셋: 짧은 샘플 이력서 3개 (서로 다른 직무로 '직무 관련성'까지 검증)
# ---------------------------------------------------------------------------
SAMPLES = [
    {
        "job_field": "AI/ML",
        "level": "신입",
        "resume": "Python, LangChain, RAG, FAISS 사용 경험. KT AIVLE School AI 트랙 수료. "
                  "개인 프로젝트로 이력서 기반 AI 면접관 에이전트(CrewAI 멀티에이전트, FastAPI, "
                  "Streamlit)를 개발하고 Hugging Face에 배포함.",
    },
    {
        "job_field": "백엔드",
        "level": "신입",
        "resume": "Java, Spring Boot, JPA, MySQL 학습. 팀 프로젝트에서 게시판 REST API 구현 "
                  "(회원가입/로그인 세션 인증, 게시글 CRUD). Git/GitHub 협업 경험. 정보처리기사 필기 합격.",
    },
    {
        "job_field": "데이터 분석",
        "level": "신입",
        "resume": "Python, Pandas, NumPy, Matplotlib, SQL 기초. 공공데이터로 따릉이 이용 패턴 "
                  "EDA 및 시각화 프로젝트 수행. 간단한 선형회귀로 수요 예측 시도. AICE Associate 보유.",
    },
]

# ---------------------------------------------------------------------------
# 프롬프트 3개 버전
# ---------------------------------------------------------------------------
def prompt_v1(resume, job_field, level):
    """V1: 약한 baseline (모델만 gpt-5-mini, 프롬프트는 원본)"""
    return f"""아래 이력서 내용을 보고 면접 질문 3개를 한국어로 만들어줘.

직무 분야: {job_field}
지원자 수준: {level}

{level}에 맞는 난이도로 {job_field} 직무에 특화된 질문을 만들어줘.
번호를 붙여서 질문만 출력하고 다른 설명은 하지마.

이력서 내용:
{resume}
"""


def prompt_v2(resume, job_field, level):
    """V2: 직무 적합성 + 난이도 기준 + 이력서 근거 (현재 코드)"""
    return f"""당신은 {job_field} 분야의 면접관입니다.
아래 이력서를 바탕으로 {level} 지원자에게 맞는 면접 질문 3개를 한국어로 만드세요.

[직무 적합성 — {job_field}]
- {job_field} 직무에서 중요하게 평가하는 핵심 역량을 기준으로 질문할 것.
- 같은 경험이라도 {job_field} 관점에서 파고들 것.

[난이도 — {level} (반드시 지킬 것)]
- 신입: 기초 개념 이해, 학습 경험, 이력서에 실제로 적힌 본인이 직접 한 것 위주.
        가정형 대규모 시스템 설계·아키텍처 의사결정 질문은 절대 금지.
- 주니어: 실무 응용, 기술 선택 이유, 간단한 트러블슈팅.
- 시니어: 시스템 설계, 트레이드오프, 확장성·일관성.

[좋은 질문의 조건]
- 이력서에 실제로 적힌 프로젝트·기술·경험을 구체적으로 지목할 것.
- 자기소개·장단점 같은 뻔한 질문 금지.
- 한 질문에는 하나의 주제만 담을 것.

[출력] 1. 2. 3. 번호를 붙여 질문만 출력. 다른 설명은 하지 말 것.

이력서 내용:
{resume}
"""


def prompt_v3(resume, job_field, level):
    """V3: V2 + 단일 주제 강제 (간결성)"""
    return f"""당신은 {job_field} 분야의 면접관입니다.
아래 이력서를 바탕으로 {level} 지원자에게 맞는 면접 질문 3개를 한국어로 만드세요.

[직무 적합성 — {job_field}]
- {job_field} 직무에서 중요하게 평가하는 핵심 역량을 기준으로 질문할 것.
- 같은 경험이라도 {job_field} 관점에서 파고들 것.

[난이도 — {level} (반드시 지킬 것)]
- 신입: 기초 개념 이해, 학습 경험, 이력서에 실제로 적힌 본인이 직접 한 것 위주.
        가정형 대규모 시스템 설계·아키텍처 의사결정 질문은 절대 금지.
- 주니어: 실무 응용, 기술 선택 이유, 간단한 트러블슈팅.
- 시니어: 시스템 설계, 트레이드오프, 확장성·일관성.

[좋은 질문의 조건]
- 이력서에 실제로 적힌 프로젝트·기술·경험을 구체적으로 지목할 것.
- 자기소개·장단점 같은 뻔한 질문 금지.

[★단일 주제 — 매우 중요]
- 한 질문은 반드시 '하나의 주제'만 물을 것.
- 'A, B, C는 각각 무엇인가요'처럼 여러 하위질문을 한 문장에 묶지 말 것.
- 각 질문은 2문장 이내로 간결하게.

[출력] 1. 2. 3. 번호를 붙여 질문만 출력. 다른 설명은 하지 말 것.

이력서 내용:
{resume}
"""


# 버전마다 (생성모델, 프롬프트)를 지정 → 변수를 하나씩만 바꿔 효과를 분리한다.
#   V0→V1: 모델 교체 효과 (프롬프트 고정)
#   V1→V2→V3: 프롬프트 개선 효과 (모델 고정)
VERSIONS = {
    "V0 (원본/4o-mini)": ("gpt-4o-mini", prompt_v1),
    "V1 (모델교체/5-mini)": ("gpt-5-mini", prompt_v1),
    "V2 (프롬프트)": ("gpt-5-mini", prompt_v2),
    "V3 (+단일주제)": ("gpt-5-mini", prompt_v3),
}


# ---------------------------------------------------------------------------
# 생성 / 파싱
# ---------------------------------------------------------------------------
def generate(prompt, model):
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=2000,
    )
    return resp.choices[0].message.content or ""


def parse_questions(text):
    questions = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if line and line[0].isdigit():
            # "1. " 같은 머리표 제거
            questions.append(re.sub(r"^\d+[.)]\s*", "", line))
    return questions[:3]


# ---------------------------------------------------------------------------
# 심사관 (LLM-as-a-judge)
# ---------------------------------------------------------------------------
JUDGE_RUBRIC = """당신은 면접 질문 품질을 평가하는 엄격한 심사관입니다.
아래 '지원자 정보'와 '면접 질문' 하나를 보고, 4개 항목을 각각 0 또는 1로 채점하세요.

채점 항목:
- level_fit: 질문이 지원자 수준({level})에 맞으면 1. 신입인데 가정형 대규모 시스템
  설계/아키텍처 의사결정을 요구하면 0.
- job_relevance: 질문이 '{job_field}' 직무의 핵심 역량을 반영하면 1, 아니면 0.
- resume_grounded: 질문이 이력서에 실제로 적힌 구체적 내용(프로젝트/기술/경험)을
  지목하면 1, 일반적·추상적이면 0.
- single_topic: 한 질문이 하나의 주제만 물으면 1. 여러 하위질문을 한 문장에 묶었으면 0.

반드시 아래 JSON 형식으로만 답하세요:
{{"level_fit": 0|1, "job_relevance": 0|1, "resume_grounded": 0|1, "single_topic": 0|1}}
"""


def judge(question, resume, job_field, level):
    sys = JUDGE_RUBRIC.format(level=level, job_field=job_field)
    user = f"지원자 정보\n- 직무: {job_field}\n- 수준: {level}\n- 이력서: {resume}\n\n면접 질문: {question}"
    resp = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
        temperature=0,
        response_format={"type": "json_object"},
        max_completion_tokens=100,
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {"level_fit": 0, "job_relevance": 0, "resume_grounded": 0, "single_topic": 0}


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------
METRICS = ["level_fit", "job_relevance", "resume_grounded", "single_topic"]
METRIC_KR = {
    "level_fit": "난이도적합",
    "job_relevance": "직무관련",
    "resume_grounded": "이력서근거",
    "single_topic": "단일주제",
}


def main():
    results = {}          # version -> metric -> [scores]
    samples_log = []      # 정성 비교용 (각 버전 첫 이력서 질문 저장)

    for vname, (model, pfn) in VERSIONS.items():
        results[vname] = defaultdict(list)
        print(f"\n{'='*60}\n[{vname}] 생성({model})·채점 중...\n{'='*60}")
        for s in SAMPLES:
            prompt = pfn(s["resume"], s["job_field"], s["level"])
            raw = generate(prompt, model)
            qs = parse_questions(raw)
            if s is SAMPLES[0]:
                samples_log.append((vname, qs))
            for q in qs:
                scores = judge(q, s["resume"], s["job_field"], s["level"])
                for m in METRICS:
                    results[vname][m].append(int(scores.get(m, 0)))
            print(f"  [{s['job_field']}] 질문 {len(qs)}개 채점 완료")

    # ---- 표 출력 ----
    print(f"\n\n{'='*60}\n  결과: 버전별 지표 통과율 (%)\n{'='*60}")
    header = "지표".ljust(12) + "".join(v.ljust(22) for v in VERSIONS)
    print(header)
    print("-" * len(header))
    lines_md = ["| 지표 | " + " | ".join(VERSIONS) + " |",
                "|---|" + "---|" * len(VERSIONS)]
    for m in METRICS:
        row = METRIC_KR[m].ljust(12)
        md_cells = []
        for v in VERSIONS:
            vals = results[v][m]
            pct = 100 * sum(vals) / len(vals) if vals else 0
            row += f"{pct:5.0f}%".ljust(22)
            md_cells.append(f"{pct:.0f}%")
        print(row)
        lines_md.append(f"| {METRIC_KR[m]} | " + " | ".join(md_cells) + " |")

    # 종합(전체 지표 평균)
    overall_md = []
    row = "종합평균".ljust(12)
    for v in VERSIONS:
        allv = [x for m in METRICS for x in results[v][m]]
        pct = 100 * sum(allv) / len(allv) if allv else 0
        row += f"{pct:5.0f}%".ljust(22)
        overall_md.append(f"{pct:.0f}%")
    print("-" * len(header))
    print(row)
    lines_md.append(f"| **종합평균** | " + " | ".join(f"**{x}**" for x in overall_md) + " |")

    # ---- results.md 저장 ----
    out = ["# 면접 질문 품질 평가 결과 (LLM-as-a-judge)", ""]
    out.append(f"- 생성 모델: 버전별 상이 (V0=`gpt-4o-mini`, V1~V3=`gpt-5-mini`) / 심사관: `{JUDGE_MODEL}` (편향 완화 위해 분리)")
    out.append(f"- 평가셋: 이력서 {len(SAMPLES)}개 × 버전당 질문 {3*len(SAMPLES)}개 채점")
    out.append("- 지표: 난이도적합 · 직무관련 · 이력서근거 · 단일주제 (각 0/1)")
    out.append("")
    out.extend(lines_md)
    out.append("")
    out.append("## 정성 비교 (첫 번째 이력서: AI/ML 신입)")
    for vname, qs in samples_log:
        out.append(f"\n### {vname}")
        for i, q in enumerate(qs, 1):
            out.append(f"{i}. {q}")
    md_path = os.path.join(os.path.dirname(__file__), "results.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"\n결과 저장: {md_path}")


if __name__ == "__main__":
    main()
