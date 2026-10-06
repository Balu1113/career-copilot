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


_EDUCATION_HEADINGS = {
    "education",
    "education details",
    "education qualifications",
    "educational background",
    "educational qualifications",
    "academic background",
    "academic qualifications",
    "academics",
    "qualifications",
    "education & training",
}

_SECTION_HEADINGS = {
    "summary",
    "professional summary",
    "profile",
    "objective",
    "about",
    "about me",
    "experience",
    "work experience",
    "professional experience",
    "employment",
    "employment history",
    "work history",
    "projects",
    "personal projects",
    "key projects",
    "skills",
    "technical skills",
    "key skills",
    "core competencies",
    "certifications",
    "certificates",
    "awards",
    "achievements",
    "publications",
    "activities",
    "volunteer",
    "interests",
    "languages",
    "additional information",
    "additional",
    "contact",
    "contact information",
    "personal details",
    "personal information",
    "references",
    "declaration",
}

_DEGREE_KEYWORDS = (
    "bachelor",
    "master",
    "doctor",
    "phd",
    "mphil",
    "diploma",
    "associate",
    "certificate",
    "degree",
    "b.tech",
    "m.tech",
    "b.sc",
    "m.sc",
    "bca",
    "mca",
    "mba",
    "bba",
    "b.eng",
    "m.eng",
    "b.e.",
    "m.e.",
    "bachelor of",
    "master of",
)

_INSTITUTION_KEYWORDS = (
    "university",
    "college",
    "institute",
    "institution",
    "school",
    "academy",
    "polytechnic",
    "iit ",
    "nit ",
)

_DATE_RANGE = re.compile(
    r"\b((?:19|20)\d{2})\s*(?:[-–—]|to|through)\s*"
    r"((?:19|20)\d{2}|present|current)\b",
    re.IGNORECASE,
)

_SINGLE_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")

_SPLIT_PARTS = re.compile(r"\s*[|,;]\s*|\s+[-–—]\s+")


def _heading_key(line):
    return line.strip().rstrip(":").strip().casefold()


def _is_all_caps_heading(line):
    stripped = line.strip()
    return (
        bool(stripped)
        and len(stripped.split()) <= 6
        and stripped == stripped.upper()
        and any(character.isalpha() for character in stripped)
    )


def _split_dates(line):
    match = _DATE_RANGE.search(line)
    if match:
        rest = (line[: match.start()] + " " + line[match.end() :]).strip()
        return match.group(1), match.group(2), rest

    match = _SINGLE_YEAR.search(line)
    if match:
        rest = (line[: match.start()] + " " + line[match.end() :]).strip()
        return match.group(0), "", rest

    return "", "", line


def _looks_like_degree(part):
    lowered = part.casefold()
    return any(keyword in lowered for keyword in _DEGREE_KEYWORDS)


def _looks_like_institution(part):
    lowered = part.casefold()
    return any(keyword in lowered for keyword in _INSTITUTION_KEYWORDS)


def _education_entry(line):
    line = line.strip().lstrip("•*-–—").strip()
    if not line or len(line.split()) < 2:
        return None

    start_date, end_date, rest = _split_dates(line)
    parts = [part.strip() for part in _SPLIT_PARTS.split(rest) if part.strip()]

    if len(parts) == 1 and re.search(r"\s+at\s+", parts[0], re.IGNORECASE):
        parts = [
            part.strip()
            for part in re.split(r"\s+at\s+", parts[0], flags=re.IGNORECASE)
            if part.strip()
        ]

    if not parts:
        return None

    degree = ""
    institution = ""
    location = ""

    degree_index = None
    for index, part in enumerate(parts):
        if _looks_like_degree(part):
            degree_index = index
            break

    if degree_index is not None:
        degree = parts[degree_index]
        remaining = parts[:degree_index] + parts[degree_index + 1 :]
    elif _looks_like_institution(parts[0]):
        institution = parts[0]
        remaining = parts[1:]
        degree = remaining.pop(0) if remaining else ""
    else:
        degree = parts[0]
        remaining = parts[1:]

        if " from " in degree.casefold():
            head, _, tail = degree.partition(" from ")
            degree = head.strip()
            remaining.insert(0, tail.strip())

    if not institution:
        for part in list(remaining):
            if _looks_like_institution(part):
                institution = part
                remaining.remove(part)
                break

    if not institution and remaining:
        institution = remaining.pop(0)

    location = ", ".join(remaining)

    if not degree and not institution:
        return None

    return {
        "degree": degree,
        "institution": institution,
        "location": location,
        "start_date": start_date,
        "end_date": end_date,
        "grade": "",
    }


def _education_from_text(resume_text):
    """Last-resort education recovery from the raw resume text."""
    lines = (resume_text or "").splitlines()

    start_index = None
    for index, line in enumerate(lines):
        if _heading_key(line) in _EDUCATION_HEADINGS:
            start_index = index
            break

    if start_index is None:
        return []

    entries = []
    for line in lines[start_index + 1 :]:
        if not line.strip():
            continue

        key = _heading_key(line)
        if key in _EDUCATION_HEADINGS or key in _SECTION_HEADINGS:
            break
        if _is_all_caps_heading(line) and not _looks_like_degree(line):
            break

        entry = _education_entry(line)
        if entry:
            entries.append(entry)
            if len(entries) >= 8:
                break

    return entries


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

    if not content.get("education"):
        candidates = [
            item
            for item in (education_fallback or [])
            if isinstance(item, dict)
            and (item.get("degree") or item.get("institution"))
        ]
        if not candidates:
            candidates = _education_from_text(resume_text or "")
        content["education"] = [
            {
                "degree": item.get("degree", ""),
                "institution": item.get("institution", ""),
                "location": item.get("location", ""),
                "start_date": item.get("start_date", ""),
                "end_date": item.get("end_date", item.get("dates", "")),
                "grade": item.get("grade", ""),
            }
            for item in candidates
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