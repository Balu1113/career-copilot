"""Build human-readable titles for generated resumes.

Kept outside the views so the generate endpoint, the wizard and any
future entry point produce titles in exactly the same shape.
"""

import re


# Matches GeneratedResume.title (models.CharField max_length=150).
MAX_TITLE_LENGTH = 150


_ROLE_LABEL = re.compile(
    r"^\s*(?:job\s*title|role|position)\s*[:\-–—]\s*(?P<value>[^\n]+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_COMPANY_LABEL = re.compile(
    r"^\s*(?:company|employer|organization|organisation)\s*[:\-–—]\s*(?P<value>[^\n]+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_HIRING_ROLE = re.compile(
    r"\b(?:we(?:\s+are|\s+'re)?\s+)?(?:hiring|seeking|looking\s+for)\s+"
    r"(?:an?\s+)?(?P<role>[A-Za-z0-9][\w+#&/.\-]*"
    r"(?:\s+(?:of|the|and|for|in|[\w+#&/.\-]+)){0,7}?)"
    r"\s+(?:to|who|with)\b",
    re.IGNORECASE,
)

_AT_COMPANY = re.compile(
    r"\bat\s+(?P<company>[A-Z][\w'&\-]*(?:\.[\w'&\-]+)*"
    r"(?:\s+[\w'&\-]+(?:\.[\w'&\-]+)*){0,5}?)"
    r"\s*(?=[.,;:]|$)",
    re.MULTILINE,
)

# Lead lines that describe a posting rather than name a role.
_GENERIC_LEAD_LINES = frozenset(
    {
        "about the role",
        "about this role",
        "about the position",
        "about the job",
        "about us",
        "about the company",
        "company overview",
        "the company",
        "the role",
        "role overview",
        "role description",
        "role responsibilities",
        "role requirements",
        "position overview",
        "job description",
        "job summary",
        "job details",
        "job overview",
        "overview",
        "summary",
        "introduction",
        "responsibilities",
        "key responsibilities",
        "requirements",
        "minimum requirements",
        "qualifications",
        "preferred qualifications",
        "required qualifications",
        "who we are",
        "who you are",
        "what you will do",
        "what you will need",
        "our ideal candidate",
        "benefits",
        "perks",
        "how to apply",
        "apply now",
        "equal opportunity employer",
        "technical skills",
        "skills",
        "education",
        "experience",
    }
)

_SENTENCE_ENDINGS = (".", "?", "!", ";")


def _clean(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _block(value):
    """Trim a pasted posting without destroying its line structure."""
    if value is None:
        return ""
    return str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


def _generic_lead_line(candidate):
    normalized = candidate.strip().rstrip(":").rstrip("-").strip().casefold()
    return normalized in _GENERIC_LEAD_LINES


def _looks_like_role(candidate):
    """Reject sentences and section headers so only real titles win."""
    if not candidate or len(candidate) > 60:
        return False
    if _generic_lead_line(candidate):
        return False
    if candidate.endswith(_SENTENCE_ENDINGS) or ":" in candidate:
        return False
    if "#" in candidate or candidate[:1].isdigit():
        return False

    words = candidate.split()
    if not 2 <= len(words) <= 8:
        return False

    lead = words[0].casefold().strip(".,")
    return lead not in {
        "we",
        "our",
        "you",
        "your",
        "the",
        "this",
        "these",
        "who",
        "why",
        "how",
        "what",
        "about",
        "seeking",
        "looking",
        "hiring",
    }


def _labeled_value(pattern, job_description):
    match = pattern.search(job_description)
    if not match:
        return ""
    return _clean(match.group("value"))


def _first_line_role(job_description):
    for line in job_description.splitlines()[:5]:
        candidate = _clean(line)
        if not candidate or not _looks_like_role(candidate):
            continue

        role, separator, trailing = candidate.partition(" at ")
        if separator and trailing and len(trailing.split()) <= 5:
            return _clean(role), _clean(trailing.rstrip("."))
        return candidate, ""

    return "", ""


def _parse_job_description(job_description):
    """Best-effort role/company extraction from a pasted posting."""
    if not job_description:
        return "", ""

    role = _labeled_value(_ROLE_LABEL, job_description)
    company = _labeled_value(_COMPANY_LABEL, job_description)
    if role or company:
        return role, company

    hiring = _HIRING_ROLE.search(job_description)
    if hiring:
        role = _clean(hiring.group("role"))
        at_match = _AT_COMPANY.search(
            job_description,
            pos=hiring.end(),
        )
        company = _clean(at_match.group("company")) if at_match else ""
        if role:
            return role, company

    return _first_line_role(job_description)


def build_generated_resume_title(
    job_description="",
    job_title="",
    company="",
    source_title="",
):
    """Compose a title from explicit inputs, the posting, or the source."""
    role = _clean(job_title)
    resolved_company = _clean(company)

    if not role or not resolved_company:
        jd_role, jd_company = _parse_job_description(
            _block(job_description)
        )
        role = role or jd_role
        resolved_company = resolved_company or jd_company

    if role and resolved_company:
        title = f"{role} - {resolved_company}"
    elif role:
        title = f"{role} Resume"
    elif resolved_company:
        title = f"{resolved_company} Resume"
    else:
        source = _clean(source_title)
        title = (
            f"Generated Resume - {source}"
            if source
            else "Generated Resume"
        )

    return title[:MAX_TITLE_LENGTH].rstrip()
