"""Shared prompt templates and helpers for resume processing.

Used by the enrichment endpoints and by the diff-based tailoring
service (``resumes.services.improver``).
"""


LANGUAGE_NAMES = {
    "ar": "Arabic",
    "bn": "Bengali",
    "bg": "Bulgarian",
    "ca": "Catalan",
    "zh": "Chinese",
    "cs": "Czech",
    "da": "Danish",
    "nl": "Dutch",
    "en": "English",
    "et": "Estonian",
    "fi": "Finnish",
    "fr": "French",
    "de": "German",
    "el": "Greek",
    "gu": "Gujarati",
    "he": "Hebrew",
    "hi": "Hindi",
    "hu": "Hungarian",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "kn": "Kannada",
    "ko": "Korean",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "ml": "Malayalam",
    "mr": "Marathi",
    "no": "Norwegian",
    "fa": "Persian",
    "pl": "Polish",
    "pt": "Portuguese",
    "pa": "Punjabi",
    "ro": "Romanian",
    "ru": "Russian",
    "sr": "Serbian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "es": "Spanish",
    "sw": "Swahili",
    "sv": "Swedish",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "vi": "Vietnamese",
}


def get_language_name(value):
    """Turn a language tag (``en``, ``pt-BR``) or a name into a name."""
    raw = str(value or "en").strip()
    if not raw:
        raw = "en"

    key = raw.lower().replace("_", "-")
    if key in LANGUAGE_NAMES:
        return LANGUAGE_NAMES[key]

    base = key.split("-", 1)[0]
    if base in LANGUAGE_NAMES:
        return LANGUAGE_NAMES[base]

    # Already a human readable name such as "French".
    if " " in raw or len(raw) > 3:
        return raw

    return LANGUAGE_NAMES["en"]


# ---------------------------------------------------------------------------
# Structured tailoring prompts
# ---------------------------------------------------------------------------

EXTRACT_KEYWORDS_PROMPT = """
Extract the structured hiring requirements from the job posting below.

Return ONLY valid JSON matching this shape:

{{
  "company": "",
  "role": "",
  "required_skills": [],
  "preferred_skills": [],
  "experience_requirements": [],
  "education_requirements": [],
  "key_responsibilities": [],
  "keywords": [],
  "experience_years": null,
  "seniority_level": ""
}}

Rules:
- Use only wording present in the posting. Never invent requirements.
- Keep technology names spelled exactly as the posting spells them.
- Leave experience_years null when the posting does not state it.

JOB POSTING:
{job_description}
"""


SKILL_TARGET_PLAN_PROMPT = """
Choose the skills this resume should emphasise for the target job.

Return ONLY valid JSON matching this shape:

{{
  "target_skills": [
    {{"skill": "Python", "reason": "Core requirement in the posting."}}
  ],
  "strategy_notes": "Short summary of the approach."
}}

Rules:
- Every target skill must appear either in the candidate's existing
  skills or in the job posting. Never invent experience.
- Prefer skills that are explicitly required by the posting.
- Keep the plan focused: at most 12 target skills.
- Write reasons and notes in {output_language}.

EXISTING SKILLS:
{existing_skills}

JOB KEYWORDS:
{job_keywords}

JOB DESCRIPTION:
{job_description}

ORIGINAL RESUME:
{original_resume}
"""


DIFF_STRATEGY_INSTRUCTIONS = {
    "keywords": (
        "Prioritise the job's required skills and recurring keywords: surface "
        "them in the summary, skills and most recent experience bullets "
        "whenever the candidate's background supports them."
    ),
    "impact": (
        "Prioritise measurable impact: strengthen existing bullets with the "
        "scope, outcomes and numbers the candidate already stated, and reorder "
        "bullets so the strongest results come first."
    ),
    "ats": (
        "Prioritise ATS readability: use the posting's exact terminology for "
        "tools and roles, keep bullets short and parseable, and move in-demand "
        "skills into the summary and skills sections."
    ),
}


DIFF_IMPROVE_PROMPT = """
Improve the resume below so it matches the target job while staying
strictly truthful to the source resume.

STRATEGY:
{strategy_instruction}

Return ONLY valid JSON matching this shape:

{{
  "changes": [
    {{
      "path": "summary",
      "action": "replace",
      "original": "exact text currently in the resume",
      "value": "replacement text"
    }}
  ],
  "strategy_notes": "Short summary of the approach."
}}

Rules:
- Allowed actions: replace, append, reorder, add_skill.
- Allowed paths start with summary, workExperience, education,
  personalProjects or additional.
- Every "original" value must be copied exactly from the resume so the
  change can be verified against it.
- Never modify personal information, dates, companies, institutions or
  degrees.
- Never invent employers, job titles, metrics, dates or achievements.
- Write new text in {output_language}.
- Return an empty changes list when nothing truthful can be improved.

TARGET SKILLS TO WORK IN:
{skill_targets}

JOB KEYWORDS:
{job_keywords}

JOB DESCRIPTION:
{job_description}

RESUME:
{original_resume}
"""


IMPROVE_SCHEMA_EXAMPLE = """
{
  "personalInfo": {
    "name": "Jane Doe",
    "title": "Software Engineer",
    "email": "jane@example.com",
    "phone": "+1-555-0123",
    "location": "Seattle, WA",
    "website": "",
    "linkedin": "",
    "github": ""
  },
  "summary": "Two to four sentence professional summary.",
  "workExperience": [
    {
      "id": 1,
      "title": "Software Engineer",
      "company": "Acme Corp",
      "location": "",
      "years": "2021 - Present",
      "description": ["Achievement with a measurable outcome."],
      "descriptionStyles": ["bullet"]
    }
  ],
  "education": [
    {
      "id": 1,
      "institution": "State University",
      "degree": "BSc Computer Science",
      "years": "2017 - 2021",
      "description": ""
    }
  ],
  "personalProjects": [],
  "additional": {
    "technicalSkills": ["Python", "Django"],
    "certificationsTraining": [],
    "languages": [],
    "awards": []
  },
  "customSections": {}
}
""".strip()


CRITICAL_TRUTHFULNESS_RULES = {
    "keywords": (
        "- Never invent employers, job titles, dates, metrics or skills.\n"
        "- Only add a skill when the candidate's resume or the job posting "
        "supports it.\n"
        "- Keep every employment entry that is already in the resume."
    ),
    "impact": (
        "- Never invent numbers, percentages or outcomes.\n"
        "- Reuse only figures the candidate already stated.\n"
        "- Do not change employers, job titles, dates or degrees."
    ),
    "ats": (
        "- Mirror the posting's wording only where it is truthful for the "
        "candidate.\n"
        "- Never invent employers, job titles, dates, metrics or skills.\n"
        "- Keep employment dates exactly as written in the resume."
    ),
}


_BASE_IMPROVE_PROMPT = """
Rewrite the resume below so it is tailored to the target job.

{critical_truthfulness_rules}

Return ONLY the complete resume JSON object matching this shape:

{schema}

Additional rules:
- Keep every field, including empty arrays, so the result is complete.
- Keep the professional summary to 2-4 sentences.
- Write the resume in {output_language}.
- Return ONLY valid JSON.

TARGET JOB DESCRIPTION:
{job_description}

TARGET JOB KEYWORDS:
{job_keywords}

ORIGINAL RESUME:
{original_resume}
"""


IMPROVE_RESUME_PROMPTS = {
    "keywords": _BASE_IMPROVE_PROMPT,
    "impact": _BASE_IMPROVE_PROMPT,
    "ats": _BASE_IMPROVE_PROMPT,
}


IMPROVE_PROMPT_OPTIONS = [
    {
        "id": "keywords",
        "label": "Keyword match",
        "description": "Align the resume with the posting's required skills.",
    },
    {
        "id": "impact",
        "label": "Achievement impact",
        "description": "Emphasise measurable outcomes and results.",
    },
    {
        "id": "ats",
        "label": "ATS readability",
        "description": "Use the posting's terminology for ATS parsers.",
    },
]
