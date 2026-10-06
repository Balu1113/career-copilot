"""Prompt templates for the resume enrichment endpoints.

Split out of the enrichment views so the wording can be reviewed and
tuned without touching request handling. Every template is a plain
``str`` and is filled with ``str.format``.
"""


ANALYZE_RESUME_PROMPT = """
You are analysing a resume to find the entries that would benefit from
concrete, measurable detail.

Return ONLY valid JSON matching this shape:

{{
  "items_to_enrich": [
    {{
      "item_id": "exp_0",
      "item_type": "experience",
      "title": "Role",
      "subtitle": "Company",
      "current_description": ["Existing bullet"],
      "weakness_reason": "Why this entry is thin."
    }}
  ],
  "questions": [
    {{
      "question_id": "q_0",
      "item_id": "exp_0",
      "question": "What changed because of this work?",
      "placeholder": "e.g., Reduced processing time by 20%"
    }}
  ],
  "analysis_summary": "Short overview of what is missing."
}}

Rules:
- Only use facts present in the resume below. Never invent employers,
  titles, dates, metrics or achievements.
- Focus on experience and project entries whose bullets lack scope,
  impact or measurable outcomes.
- Ask at most 6 questions in total, and at most 2 questions per item.
- Each question must be answerable by the candidate from their own
  memory of the work.
- Keep question text short, specific and in {output_language}.
- item_id must be one of the identifiers you listed under
  items_to_enrich (exp_<index> for experience, proj_<index> for
  projects).

RESUME JSON:
{resume_json}
"""


ENHANCE_DESCRIPTION_PROMPT = """
You strengthen one resume entry with facts supplied by the candidate.

Return ONLY valid JSON matching this shape:

{{
  "additional_bullets": ["One concrete, measurable bullet"]
}}

Rules:
- Write 1 to 4 bullets in {output_language}.
- Use ONLY facts stated in the candidate answers below. Never invent
  employers, tools, dates, percentages or achievements.
- Do not repeat bullets that are already in the current description.
- Keep each bullet to a single line, starting with a strong verb.
- Do not use first person pronouns.

ENTRY
Type: {item_type}
Title: {title}
Subtitle: {subtitle}

CURRENT DESCRIPTION:
{current_description}

CANDIDATE ANSWERS:
{answers}
"""


REGENERATE_ITEM_PROMPT = """
Rewrite one resume entry following the candidate's instruction.

Return ONLY valid JSON matching this shape:

{{
  "new_bullets": ["First line", "Second line"],
  "change_summary": "Short description of what changed."
}}

Rules:
- Return 2 to 5 bullets in {output_language}.
- Use only facts already present in the current description or in the
  instruction. Never invent employers, tools, dates or metrics.
- Keep every claim truthful and verifiable by the candidate.
- Do not add personal pronouns.

ENTRY
Type: {item_type}
Title: {title}
Subtitle: {subtitle}

CURRENT DESCRIPTION:
{current_description}

CANDIDATE INSTRUCTION:
{user_instruction}
"""


REGENERATE_SKILLS_PROMPT = """
Rewrite one skills category following the candidate's instruction.

Return ONLY valid JSON matching this shape:

{{
  "new_skills": ["skill", "skill"],
  "change_summary": "Short description of what changed."
}}

Rules:
- Return a list of skills in {output_language}.
- Keep every skill the candidate actually has; never add skills that
  are not supported by their resume or instruction.
- Preserve spelling and common capitalisation of technology names.
- Do not use first person pronouns.

CURRENT SKILLS:
{current_skills}

CANDIDATE INSTRUCTION:
{user_instruction}
"""
