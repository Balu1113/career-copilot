
from .graph import build_career_graph


graph = build_career_graph()


initial_state = {
    "job_description": """
    We are looking for an AI Engineer with experience
    in Python, Django, REST APIs, LLMs, RAG, LangChain,
    vector databases and GenAI.
    """,

    "resume_context": """
    Candidate has experience with Python, Django,
    Django REST Framework and PostgreSQL.

    Candidate has worked on RAG chatbots and
    AI-related applications.

    Candidate has experience building backend APIs
    using Django.
    """,
}


result = graph.invoke(initial_state)


print("\nJOB REQUIREMENTS:")
print(result["job_requirements"])

print("\nRESUME ANALYSIS:")
print(result["resume_analysis"])

print("\nSKILL GAP:")
print(result["skill_gap_analysis"])

print("\nCAREER RECOMMENDATION:")
print(result["career_recommendation"])