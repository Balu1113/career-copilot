import json

from rag.services.llm import get_llm_client, get_llm_model


def generate_interview_prep(resume_context, job_description):
    client = get_llm_client()

    system_prompt = """
You are an AI Interview Preparation Assistant.

Analyze the candidate's resume context against the provided job
description and create personalized interview preparation.

Return ONLY valid JSON in exactly this structure:

{
    "technical_questions": [
        {
            "question": "...",
            "why_asked": "...",
            "preparation_hint": "..."
        }
    ],
    "resume_questions": [
        {
            "question": "...",
            "focus_area": "..."
        }
    ],
    "project_questions": [
        {
            "question": "...",
            "focus_area": "..."
        }
    ],
    "hr_questions": [
        {
            "question": "...",
            "preparation_hint": "..."
        }
    ],
    "topics_to_revise": [],
    "preparation_strategy": []
}

Rules:
1. Use the resume context and job description.
2. Do not invent experience or projects.
3. Questions should be relevant to the target role.
4. Resume and project questions must be based on information
   actually present in the resume context.
5. Keep the output concise and practical.
6. Return only valid JSON.
"""

    user_prompt = f"""
RESUME CONTEXT:
{resume_context}

JOB DESCRIPTION:
{job_description}

Generate personalized interview preparation.
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
        temperature=0.2,
    )

    content = response.choices[0].message.content

    return json.loads(content)