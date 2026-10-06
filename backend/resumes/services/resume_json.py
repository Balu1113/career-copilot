"""Helpers for working with the structured resume JSON payload."""

from __future__ import annotations

import json
import re
from typing import Any

MONTH_PATTERN = re.compile(
    r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
    re.IGNORECASE,
)

LIST_FIELDS = (
    "technicalSkills",
    "certificationsTraining",
    "languages",
    "awards",
)

SECTION_KEYS = (
    "personalInfo",
    "summary",
    "workExperience",
    "education",
    "personalProjects",
    "additional",
    "customSections",
)


def has_month(date_str: str) -> bool:
    """Return True if the date string contains a month name."""
    return bool(MONTH_PATTERN.search(date_str))


def normalize_resume_data(data: Any) -> dict[str, Any]:
    """Apply lazy migrations: ensure required keys and aligned styles."""
    if not isinstance(data, dict):
        return {}

    normalized = dict(data)

    defaults: dict[str, Any] = {
        "personalInfo": {},
        "summary": "",
        "workExperience": [],
        "education": [],
        "personalProjects": [],
        "additional": {},
        "customSections": {},
    }
    for key, default in defaults.items():
        normalized.setdefault(key, default)

    if not isinstance(normalized.get("personalInfo"), dict):
        normalized["personalInfo"] = {}
    if not isinstance(normalized.get("additional"), dict):
        normalized["additional"] = {}
    for field in LIST_FIELDS:
        value = normalized["additional"].get(field)
        if not isinstance(value, list):
            normalized["additional"][field] = []
    if not isinstance(normalized.get("customSections"), dict):
        normalized["customSections"] = {}
    for key in ("workExperience", "education", "personalProjects"):
        if not isinstance(normalized.get(key), list):
            normalized[key] = []

    for key in ("workExperience", "personalProjects"):
        for entry in normalized[key]:
            if not isinstance(entry, dict):
                continue
            description = entry.get("description")
            if not isinstance(description, list):
                entry["description"] = []
            styles = entry.get("descriptionStyles")
            if not isinstance(styles, list) or len(styles) != len(entry["description"]):
                entry["descriptionStyles"] = ["bullet"] * len(entry["description"])

    for section in normalized["customSections"].values():
        if not isinstance(section, dict):
            continue
        if section.get("sectionType") != "itemList":
            continue
        items = section.get("items")
        if not isinstance(items, list):
            section["items"] = []
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            description = item.get("description")
            if not isinstance(description, list):
                item["description"] = []
            styles = item.get("descriptionStyles")
            if not isinstance(styles, list) or len(styles) != len(description):
                item["descriptionStyles"] = ["bullet"] * len(description)

    return normalized


def has_meaningful_resume_content(data: Any) -> bool:
    """True when structured data carries actual resume content."""
    if not isinstance(data, dict):
        return False
    if str(data.get("summary") or "").strip():
        return True
    for key in ("workExperience", "education", "personalProjects"):
        entries = data.get(key)
        if isinstance(entries, list) and entries:
            return True
    additional = data.get("additional")
    if isinstance(additional, dict):
        for field in LIST_FIELDS:
            if additional.get(field):
                return True
    custom = data.get("customSections")
    if isinstance(custom, dict) and custom:
        return True
    return False


def original_resume_data(resume: dict[str, Any] | Any) -> dict[str, Any] | None:
    """Structured source data for a resume record."""
    if hasattr(resume, "processed_data"):
        processed = resume.processed_data
        content_type = resume.content_type
        content = resume.extracted_text
    else:
        processed = resume.get("processed_data")
        content_type = resume.get("content_type")
        content = resume.get("content")

    if processed:
        return normalize_resume_data(processed)

    if content_type == "json" and isinstance(content, str) and content:
        try:
            return normalize_resume_data(json.loads(content))
        except json.JSONDecodeError as exc:
            # Skipping resume diff due to JSON parse failure.
            return None
    return None


def original_source_text(resume: dict[str, Any] | Any) -> str:
    """Source text captured at upload time (markdown/text snapshot)."""
    if hasattr(resume, "original_markdown"):
        original = resume.original_markdown
        content_type = resume.content_type
        content = resume.extracted_text
    else:
        original = resume.get("original_markdown")
        content_type = resume.get("content_type")
        content = resume.get("content") or resume.get("extracted_text") or ""

    if original and isinstance(original, str):
        return original
    if content_type == "md" and isinstance(content, str) and content:
        return content
    if isinstance(content, str) and content:
        return content
    return ""
