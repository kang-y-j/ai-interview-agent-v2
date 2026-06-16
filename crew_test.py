import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM

load_dotenv()

llm = LLM(model="gpt-4o-mini")

interviewer = Agent(
    role="interviewer",
    goal="Create key interview questions by analyzing the applicant's resume",
    backstory="You are a professional interviewer specializing in AI developer hiring.",
    llm=llm,
    verbose=True
)

evaluator = Agent(
    role="evaluator",
    goal="Review and improve the quality of interview questions",
    backstory="You are a hiring consultant who specializes in improving question quality.",
    llm=llm,
    verbose=True
)

task1 = Task(
    description="Review the resume below and create 3 interview questions in Korean.\n\nResume: Python, LangChain, LangGraph, RAG skills. KT AIVLE School AI developer track completed. AI interview agent project experience.",
    expected_output="3 interview questions in Korean",
    agent=interviewer
)

task2 = Task(
    description="Review the generated interview questions and make them sharper. Answer in Korean.",
    expected_output="3 improved interview questions in Korean",
    agent=evaluator
)

crew = Crew(agents=[interviewer, evaluator], tasks=[task1, task2], verbose=True)
result = crew.kickoff()
print("\n=== 최종 결과 ===")
print(result)