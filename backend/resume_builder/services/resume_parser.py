from agents.services.structured_llm import (
    generate_structured_output,
)

from resume_builder.schemas import (
    GeneratedResumeContent,
)


RESUME_PARSER_SYSTEM_PROMPT = """
You are a resume information extraction assistant.

Extract structured information from the provided resume text.

IMPORTANT:
- Extract ONLY information explicitly present in the resume.
- Do NOT invent information.
- Do NOT improve or rewrite the content.
- Preserve the original meaning and facts.
- Do NOT add skills that are not present.
- Do NOT add projects that are not present.
- Do NOT create experience.
- Do NOT create achievements or metrics.
- If information is unavailable, use an empty string or empty list.
- Preserve dates exactly when possible.
- Preserve company names and job titles exactly.
- Preserve project names and technologies from the source.

Return ONLY valid JSON matching the requested schema.
"""


RESUME_PARSER_USER_PROMPT = """
Extract the following resume into the structured format.

RESUME TEXT:
{resume_text}

Return:
- personal information
- professional summary
- skills
- work experience
- projects
- education
- certifications
- publications

Do not invent or modify information.
"""


def parse_resume_text(resume_text):
    if not resume_text or not resume_text.strip():
        raise ValueError(
            "Resume text is empty."
        )

    prompt = RESUME_PARSER_USER_PROMPT.format(
        resume_text=resume_text,
    )

    return generate_structured_output(
        system_prompt=RESUME_PARSER_SYSTEM_PROMPT,
        user_prompt=prompt,
        schema=GeneratedResumeContent,
    )