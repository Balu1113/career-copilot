import json

from rag.services.llm import (
    get_llm_client,
    get_llm_model,
)


def analyze_job_description(
    resume_context,
    job_description,
):
    client = get_llm_client()

    system_prompt = """
You are an AI Career Copilot that analyzes a candidate's
resume against a job description.

Return ONLY valid JSON.

The JSON must contain:

{
    "match_summary": "...",
    "matching_skills": [],
    "missing_skills": [],
    "relevant_experience": [],
    "skill_gaps": [],
    "recommended_preparation": []
}

Rules:

1. Use only information present in the resume context
   when describing the candidate.
2. Do not invent candidate experience.
3. Identify skills explicitly required by the job.
4. Distinguish between skills the candidate has and skills
   that are not demonstrated in the resume.
5. Keep recommendations practical.
"""

    user_prompt = f"""
RESUME CONTEXT:

{resume_context}


JOB DESCRIPTION:

{job_description}
"""

    response = client.chat.completions.create(
        model=get_llm_model(),
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.1,
    )

    content = response.choices[0].message.content

    return json.loads(content)