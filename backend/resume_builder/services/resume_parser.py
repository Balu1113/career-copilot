import re

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

Prioritize extracting the person's name and every education entry. Do not
leave these fields empty when the resume text explicitly contains them.
"""


def _fallback_name(resume_text):
    ignored_headings = {
        "curriculum vitae",
        "resume",
        "cv",
        "profile",
        "contact",
        "education",
        "projects",
        "technical skills",
        "skills",
        "certifications",
        "experience",
    }

    for line in resume_text.splitlines()[:6]:
        candidate = re.sub(r"^[\W_]+|[\W_]+$", "", line).strip()
        normalized = candidate.casefold()
        if (
            normalized in ignored_headings
            or "@" in candidate
            or ":" in candidate
            or re.search(r"\d|https?://|www\.", candidate, re.IGNORECASE)
            or len(candidate.split()) not in range(2, 6)
            or not re.fullmatch(r"[^\W\d_][\w .'-]+", candidate)
        ):
            continue
        return candidate

    return ""


def complete_resume_content(content, resume_text, education_fallback=None):
    """Fill parser omissions from explicit source text or saved extraction."""
    content = dict(content or {})
    personal = dict(content.get("personal") or {})

    email_match = re.search(
        r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
        resume_text or "",
    )
    phone_match = re.search(
        r"(?<!\w)(?:\+?\d[\d\s().-]{8,}\d)(?!\w)",
        resume_text or "",
    )
    phone = phone_match.group(0).strip() if phone_match else ""
    if phone and sum(character.isdigit() for character in phone) < 10:
        phone = ""

    fallbacks = {
        "name": _fallback_name(resume_text or ""),
        "email": email_match.group(0) if email_match else "",
        "phone": phone,
    }
    for field, value in fallbacks.items():
        if not personal.get(field) and value:
            personal[field] = value
    content["personal"] = personal

    if not content.get("education") and education_fallback:
        content["education"] = [
            {
                "degree": item.get("degree", ""),
                "institution": item.get("institution", ""),
                "location": item.get("location", ""),
                "start_date": item.get("start_date", ""),
                "end_date": item.get("end_date", item.get("dates", "")),
                "grade": item.get("grade", ""),
            }
            for item in education_fallback
            if isinstance(item, dict)
            and (item.get("degree") or item.get("institution"))
        ]

    return content


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