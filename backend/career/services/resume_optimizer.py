from agents.services.structured_llm import generate_structured_output
from agents.schemas import ResumeOptimization


def optimize_resume_for_job(resume_context, job_description, job_requirements):
    system_prompt = """
You are a resume optimization assistant. Optimize only from evidence in
the candidate's existing resume and never invent experience or metrics.
""".strip()

    user_prompt = f"""
Optimize the candidate's existing resume for the provided job description.

STRICT RULES:
- Never invent experience, projects, skills, tools, certifications, education, or achievements.
- Only recommend changes supported by the resume.
- Do not turn a missing skill into a demonstrated skill.
- Do not fabricate metrics.
- Preserve the candidate's actual experience.
- Suggestions should improve ATS relevance and clarity.
- If a requirement is missing from the resume, explicitly mark it as missing.
- Existing bullets may be rewritten, but their factual meaning must remain true.

RESUME:
{resume_context}

JOB REQUIREMENTS:
{job_requirements}

JOB DESCRIPTION:
{job_description}

Return:
1. requirements that are already supported
2. missing requirements
3. resume sections that should be improved
4. rewritten bullets based only on existing evidence
5. ATS keywords that can safely be incorporated
6. final optimization summary
"""

    return generate_structured_output(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=ResumeOptimization,
        max_retries=2,
    )