import re

from agents.schemas import ResumeIntelligence
from agents.services.structured_llm import generate_structured_output


SUMMARY_HEADINGS = {
    "summary",
    "professional summary",
    "profile",
    "career summary",
    "objective",
    "career objective",
}


def extract_explicit_summary(resume_text: str) -> str:
    """
    Extract only an explicitly labelled summary/profile/objective section.

    If no recognised heading exists, return an empty string.
    """

    if not resume_text:
        return ""

    lines = [line.strip() for line in resume_text.splitlines()]

    for index, line in enumerate(lines):
        heading = re.sub(r"[^a-zA-Z ]", "", line).strip().lower()

        if heading not in SUMMARY_HEADINGS:
            continue

        summary_lines = []

        for next_line in lines[index + 1:]:
            cleaned = next_line.strip()

            if not cleaned:
                if summary_lines:
                    break
                continue

            next_heading = re.sub(
                r"[^a-zA-Z ]",
                "",
                cleaned
            ).strip().lower()

            # Stop when another recognised resume section begins.
            if next_heading in {
                "skills",
                "technical skills",
                "experience",
                "work experience",
                "professional experience",
                "employment",
                "projects",
                "education",
                "certifications",
                "achievements",
                "internship",
                "internships",
                "languages",
            }:
                break

            summary_lines.append(cleaned)

        return " ".join(summary_lines).strip()

    return ""


SYSTEM_PROMPT = """
You are the Resume Intelligence extraction agent.

The resume is the ONLY source of truth.

STRICT RULES:

1. Extract only information explicitly present in the resume.
2. Never invent information.
3. Never infer technologies, responsibilities, achievements, projects,
   qualifications, or experience.
4. Keep projects separate from professional experience.
5. Keep different employment entries separate.
6. Do not create information that is not present in the resume.

PROFESSIONAL SUMMARY:

The professional_summary field is provided separately by the application.

DO NOT generate, rewrite, summarize, or infer a professional summary.

Return the professional_summary field exactly as provided in the user
input.

SKILLS:

Extract only explicitly mentioned skills.

PROJECTS:

Extract only explicitly listed projects.

For every project return:

- name
- description
- technologies

EXPERIENCE:

Extract only actual employment/internship experience.

For every experience entry return:

- company
- role
- description
- technologies

EDUCATION:

Extract explicitly listed education.

For every education entry return:

- institution
- degree
- dates

CERTIFICATIONS:

Extract explicitly listed certifications.

For every certification return:

- name
- issuer

GENERAL:

If information is unavailable, use the appropriate empty value.

Return ONLY valid JSON matching the ResumeIntelligence schema.
"""


def generate_resume_intelligence(resume_text):
    explicit_summary = extract_explicit_summary(resume_text)

    user_prompt = f"""
Extract structured resume intelligence from the resume below.

================ RESUME =================

{resume_text}

============== END RESUME ================

IMPORTANT:

The application has already determined the professional summary.

The value is:

professional_summary = {explicit_summary!r}

You MUST return that exact value for professional_summary.

DO NOT generate another summary.

DO NOT rewrite it.

DO NOT create a summary from skills, projects, experience, education,
certifications, or technologies.

PROJECTS:

Look for sections such as:

- Projects
- Academic Projects
- Personal Projects
- Major Projects
- Project Work

For every project return:

- name
- description
- technologies

Do not move project descriptions into experience.

EXPERIENCE:

Look for:

- Experience
- Work Experience
- Professional Experience
- Employment
- Internship
- Internships

For every experience entry return:

- company
- role
- description
- technologies

Keep different companies and roles separate.

SKILLS:

Extract only explicitly mentioned skills.

Return:

- skills
- programming_languages
- frameworks
- tools_and_technologies
- ai_ml_technologies

EDUCATION:

Return:

- institution
- degree
- dates

CERTIFICATIONS:

Return:

- name
- issuer

Do not invent missing information.

Return ONLY valid JSON matching the schema.
"""

    result = generate_structured_output(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=ResumeIntelligence,
    )

    data = result.model_dump()

    # Final application-level enforcement.
    # The LLM cannot override this field.
    data["professional_summary"] = explicit_summary

    return data