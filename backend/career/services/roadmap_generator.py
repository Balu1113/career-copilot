from agents.services.structured_llm import generate_structured_output
from career.schemas import CareerRoadmapOutput


def generate_career_roadmap(
    *,
    skill_gap_analysis,
    career_recommendation,
    resume_intelligence=None,
    job_description="",
    target_role="",
):
    system_prompt = """
You are a career roadmap planning agent. Create practical, sequential,
evidence-based learning plans without inventing candidate experience.
""".strip()

    user_prompt = f"""
Create a practical, personalized learning roadmap for the candidate
using ONLY the information provided below.

TARGET ROLE:
{target_role or "Infer the target role from the job description."}

TARGET JOB DESCRIPTION:
{job_description}

RESUME INTELLIGENCE:
{resume_intelligence or {}}

SKILL GAP ANALYSIS:
{skill_gap_analysis}

CAREER RECOMMENDATION:
{career_recommendation}

STRICT RULES:

1. Prioritize skills explicitly identified as gaps.
2. Do not invent unrelated skills.
3. Do not claim the candidate already knows a missing skill.
4. Separate learning topics from hands-on projects.
5. Projects must address actual identified skill gaps.
6. Use the candidate's existing skills as prerequisites when appropriate.
7. Prioritize important job requirements over minor requirements.
8. Keep the roadmap practical and sequential.
9. Do not fabricate experience, achievements, certifications, or projects.
10. Do not recommend certifications unless they are specifically relevant.
11. Every recommended skill should have a clear reason.
12. Every learning topic should have a measurable learning outcome.
13. Projects should be realistic portfolio projects.
14. Avoid repeating the same skill unnecessarily across phases.

Create:

- roadmap title
- target role
- concise roadmap summary
- skills to learn
- learning topics
- practical projects
- sequential learning phases
- immediate next steps

Return only the requested structured output.
"""

    return generate_structured_output(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=CareerRoadmapOutput,
        max_retries=2,
    )