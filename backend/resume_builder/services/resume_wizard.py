"""Conversation state machine for the guided resume wizard.

The view owns HTTP concerns; everything about how a turn changes the
draft lives here so it can be tested without a request.
"""

import copy
import json

from agents.services.structured_llm import generate_structured_output

from .resume_processing_prompts import get_language_name
from resume_builder.resume_wizard_schemas import (
    ResumeWizardResumeData,
    ResumeWizardTurnOutput,
)


RESUME_WIZARD_MAX_QUESTIONS = 20

MAX_HISTORY = 30

# Section the candidate is answering -> the resume_data field it edits.
_SECTION_TARGETS = {
    "intro": (None, None),
    "contact": ("personalInfo", "mapping"),
    "summary": ("summary", "scalar"),
    "workExperience": ("workExperience", "entries"),
    "internships": ("workExperience", "entries"),
    "education": ("education", "entries"),
    "personalProjects": ("personalProjects", "entries"),
    "skills": ("additional", "mapping"),
    "review": (None, None),
}

_ENTRY_FIELDS = {"workExperience", "education", "personalProjects"}

_INTRO_QUESTION = {
    "text": "Let's build your resume. What name should appear at the top?",
    "section": "intro",
}


WIZARD_SYSTEM_PROMPT = """
You are a helpful career coach interviewing a candidate to build their
resume, one section at a time.

Rules:
- Ask exactly one short question per turn and update only the section
  named in "current_section".
- Use only facts the candidate gives you. Never invent employers,
  titles, dates, degrees, metrics or skills.
- Keep every other section of the resume exactly as it is.
- Preserve the "id" of every existing resume entry; use id 0 only for
  entries you are adding.
- When the resume is complete, set is_complete to true and move
  next_question.section to "review".
- Return ONLY valid JSON matching the requested schema.
"""


WIZARD_TURN_USER_PROMPT = """
Continue the resume wizard.

CURRENT SECTION: {current_section}
QUESTIONS ASKED SO FAR: {asked_count} of {max_questions}
OUTPUT LANGUAGE: {output_language}

Section guidance:
{section_guidance}

CANDIDATE ANSWER:
{answer}
{skip_note}

CURRENT RESUME DATA:
{resume_json}

Return ONLY valid JSON:
{{
  "resume_data": {{ ... updated resume data ... }},
  "next_question": {{"text": "...", "section": "..."}},
  "inferred_skills": ["..."],
  "is_complete": false
}}
"""


SECTION_GUIDANCE = {
    "intro": (
        "- Greet the candidate and ask for the full name they want on the "
        "resume."
    ),
    "contact": (
        "- Collect contact details: email, phone, location and optional "
        "links (LinkedIn, GitHub, portfolio)."
    ),
    "summary": (
        "- Draft a 2-4 sentence professional summary using only facts the "
        "candidate already shared."
    ),
    "workExperience": (
        "- Collect work experience: job title, company, dates and 2-4 "
        "achievement bullets per role."
    ),
    "internships": (
        "- Collect internships and volunteer roles in the same detail as "
        "work experience."
    ),
    "education": (
        "- Collect education: institution, degree, dates and notable "
        "achievements."
    ),
    "personalProjects": (
        "- Collect personal projects: name, your role, links and outcome "
        "bullets."
    ),
    "skills": (
        "- Collect technical skills, tools and certifications the "
        "candidate actually has."
    ),
    "review": (
        "- The resume is complete. Summarise what is ready and offer to "
        "revise any section."
    ),
}


def _string_list(value):
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def build_initial_wizard_state():
    return {
        "current_section": "intro",
        "asked_count": 0,
        "resume_data": {
            "personalInfo": {},
            "summary": "",
            "workExperience": [],
            "education": [],
            "personalProjects": [],
            "additional": {"technicalSkills": []},
            "sectionMeta": [],
            "customSections": {},
        },
        "next_question": dict(_INTRO_QUESTION),
        "inferred_skills": [],
        "is_complete": False,
        "history": [],
    }


def _snapshot(state):
    snapshot = {
        key: value for key, value in state.items() if key != "history"
    }
    return copy.deepcopy(snapshot)


def _push_history(state):
    history = list(state.get("history") or [])
    history.append(_snapshot(state))
    return history[-MAX_HISTORY:]


def _has_required_content(resume_data):
    if not isinstance(resume_data, dict):
        return False
    personal = resume_data.get("personalInfo") or {}
    has_name = bool(str(personal.get("name") or "").strip())
    has_entry = any(
        resume_data.get(section)
        for section in _ENTRY_FIELDS
    )
    return has_name and has_entry


def apply_back(state):
    history = list(state.get("history") or [])
    if not history:
        return dict(state)

    previous = dict(history.pop())
    previous["history"] = history
    return previous


def apply_review(state):
    resume_data = state.get("resume_data") or {}
    updated = dict(state)
    updated["current_section"] = "review"
    updated["is_complete"] = bool(state.get("is_complete")) or (
        _has_required_content(resume_data)
    )
    updated["history"] = _push_history(state)
    return updated


def _preserve_entry_ids(existing_entries, incoming_entries):
    """Keep known entry ids; every new entry starts at id 0."""
    known_ids = set()
    for entry in existing_entries:
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id")
        if (
            isinstance(entry_id, int)
            and not isinstance(entry_id, bool)
            and entry_id > 0
        ):
            known_ids.add(entry_id)

    used_ids = set()
    merged = []
    for entry in incoming_entries:
        if not isinstance(entry, dict):
            continue
        entry = dict(entry)
        entry_id = entry.get("id")
        if (
            isinstance(entry_id, int)
            and not isinstance(entry_id, bool)
            and entry_id > 0
            and entry_id in known_ids
            and entry_id not in used_ids
        ):
            used_ids.add(entry_id)
        else:
            entry["id"] = 0
        merged.append(entry)
    return merged


def _merge_current_section(resume_data, llm_resume_data, current_section):
    target = _SECTION_TARGETS.get(current_section, (None, None))
    key, kind = target
    if key is None:
        return resume_data

    incoming = llm_resume_data.get(key)

    if kind == "scalar":
        if isinstance(incoming, str):
            resume_data[key] = incoming
        return resume_data

    if kind == "mapping":
        current = resume_data.get(key)
        current = dict(current) if isinstance(current, dict) else {}
        if isinstance(incoming, dict):
            current.update(incoming)
        resume_data[key] = current
        return resume_data

    current = resume_data.get(key)
    current = list(current) if isinstance(current, list) else []
    if not isinstance(incoming, list):
        incoming = current
    if key in _ENTRY_FIELDS:
        incoming = _preserve_entry_ids(current, incoming)
    resume_data[key] = incoming
    return resume_data


def run_ai_turn(state, answer_text, *, skip=False, output_language="en"):
    """Ask the model for the next wizard step and merge its answer."""
    current_section = state.get("current_section") or "intro"
    resume_data = state.get("resume_data") or {}

    prompt = WIZARD_TURN_USER_PROMPT.format(
        current_section=current_section,
        asked_count=int(state.get("asked_count") or 0),
        max_questions=RESUME_WIZARD_MAX_QUESTIONS,
        output_language=get_language_name(output_language),
        section_guidance=SECTION_GUIDANCE.get(
            current_section,
            SECTION_GUIDANCE["intro"],
        ),
        answer=str(answer_text or "").strip() or "(No answer provided.)",
        skip_note=(
            "- The candidate skipped this question. Leave the section "
            "unchanged and ask the next question."
            if skip
            else ""
        ),
        resume_json=json.dumps(
            resume_data,
            ensure_ascii=False,
            indent=2,
        ),
    )

    raw_result = generate_structured_output(
        system_prompt=WIZARD_SYSTEM_PROMPT,
        user_prompt=prompt,
        schema=ResumeWizardTurnOutput,
    )

    if isinstance(raw_result, ResumeWizardTurnOutput):
        output = raw_result
    else:
        output = ResumeWizardTurnOutput.model_validate(raw_result)

    output_data = output.resume_data.model_dump()
    merged_data = _merge_current_section(
        dict(resume_data),
        output_data,
        current_section,
    )
    next_question = output.next_question.model_dump()

    updated = dict(state)
    updated.update(
        {
            "resume_data": merged_data,
            "asked_count": int(state.get("asked_count") or 0) + 1,
            "current_section": (
                "review"
                if output.is_complete
                else next_question.get("section") or current_section
            ),
            "next_question": next_question,
            "inferred_skills": list(output.inferred_skills),
            "is_complete": bool(output.is_complete),
            "history": _push_history(state),
        }
    )
    return updated


def normalize_resume_data(data):
    """Validate and normalise wizard data before it is stored."""
    if not isinstance(data, dict):
        raise ValueError("Resume data must be a JSON object.")

    validated = ResumeWizardResumeData.model_validate(data)
    return validated.model_dump()


def _split_years(value):
    text = str(value or "").strip()
    if not text:
        return "", "", False

    for separator in (" – ", " — ", " - ", " to ", "-"):
        if separator not in text:
            continue
        start, _, end = text.partition(separator)
        start = start.strip()
        end = end.strip()
        if not end:
            return start, "", False
        if end.casefold() in {"present", "current", "now"}:
            return start, "", True
        return start, end, False

    return text, "", False


def _experience_entries(entries):
    experience = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        start_date, end_date, current = _split_years(
            entry.get("years")
        )
        experience.append(
            {
                "company": str(entry.get("company") or ""),
                "role": str(entry.get("title") or ""),
                "location": str(entry.get("location") or ""),
                "start_date": start_date,
                "end_date": end_date,
                "current": current,
                "bullets": _string_list(entry.get("description")),
            }
        )
    return experience


def _project_entries(entries):
    projects = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        projects.append(
            {
                "name": str(entry.get("name") or ""),
                "description": "",
                "technologies": _string_list(entry.get("technologies")),
                "url": str(entry.get("url") or ""),
                "bullets": _string_list(entry.get("description")),
            }
        )
    return projects


def _education_entries(entries):
    education = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        start_date, end_date, _ = _split_years(entry.get("years"))
        education.append(
            {
                "degree": str(entry.get("degree") or ""),
                "institution": str(entry.get("institution") or ""),
                "location": str(entry.get("location") or ""),
                "start_date": start_date,
                "end_date": end_date,
                "grade": str(entry.get("grade") or ""),
            }
        )
    return education


def _skills(additional):
    skills = {}
    technical = _string_list(additional.get("technicalSkills"))
    if technical:
        skills["Technical Skills"] = technical

    languages = _string_list(additional.get("languages"))
    if languages:
        skills["Languages"] = languages

    awards = _string_list(additional.get("awards"))
    if awards:
        skills["Awards"] = awards

    return skills


def wizard_data_to_generated_content(data):
    """Convert wizard data into the renderer's resume content shape."""
    personal_info = data.get("personalInfo") or {}
    additional = data.get("additional") or {}

    certifications = [
        {"name": str(name), "issuer": "", "date": "", "url": ""}
        for name in _string_list(
            additional.get("certificationsTraining")
        )
    ]

    return {
        "personal": {
            "name": str(personal_info.get("name") or ""),
            "email": str(personal_info.get("email") or ""),
            "phone": str(personal_info.get("phone") or ""),
            "location": str(personal_info.get("location") or ""),
            "linkedin": str(personal_info.get("linkedin") or ""),
            "github": str(personal_info.get("github") or ""),
            "website": str(personal_info.get("website") or ""),
        },
        "summary": str(data.get("summary") or ""),
        "skills": _skills(additional),
        "experience": _experience_entries(
            data.get("workExperience") or []
        ),
        "projects": _project_entries(
            data.get("personalProjects") or []
        ),
        "education": _education_entries(data.get("education") or []),
        "certifications": certifications,
        "publications": [],
        "wizard_data": data,
    }
