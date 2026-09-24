from agents.schemas import InterviewAnswerEvaluation
from agents.services.structured_llm import generate_structured_output


def evaluate_interview_answer(
    question,
    category,
    difficulty,
    user_answer,
    resume_context,
    job_requirements,
):
    system_prompt = """
You are an AI interview evaluator for a career preparation platform.

Evaluate the candidate's answer using:
1. The interview question.
2. The candidate's resume evidence.
3. The job requirements.

Rules:
- Do not invent candidate experience.
- Do not assume a technology is known unless supported by the resume.
- Evaluate technical correctness, relevance, completeness, and clarity.
- Be constructive.
- A score must be between 0 and 100.
- Missing information should be identified explicitly.
- Do not penalize the candidate for using different wording when the
  underlying technical concept is correct.
"""

    user_prompt = f"""
Interview question:
{question}

Category:
{category}

Difficulty:
{difficulty}

Candidate answer:
{user_answer}

Resume context:
{resume_context}

Job requirements:
{job_requirements}

Evaluate the candidate's answer.
"""

    return generate_structured_output(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=InterviewAnswerEvaluation,
    )