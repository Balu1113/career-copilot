"""Diff-based resume tailoring: keyword extraction, change generation, apply.

Ported from the original resume management endpoints (improver service).
"""

from __future__ import annotations

import copy
import json
import logging
import re
from typing import Any

from agents.services.structured_llm import generate_structured_output
from resume_builder.services.resume_processing_prompts import (
    CRITICAL_TRUTHFULNESS_RULES,
    DIFF_IMPROVE_PROMPT,
    DIFF_STRATEGY_INSTRUCTIONS,
    EXTRACT_KEYWORDS_PROMPT,
    IMPROVE_PROMPT_OPTIONS,
    IMPROVE_RESUME_PROMPTS,
    IMPROVE_SCHEMA_EXAMPLE,
    SKILL_TARGET_PLAN_PROMPT,
    get_language_name,
)

from ..schemas import (
    JobKeywords,
    ResumeChange,
    ResumeData,
    ResumeDiffOutput,
    ResumeDiffSummary,
    ResumeFieldDiff,
    SkillTargetPlanOutput,
)
from .resume_json import normalize_resume_data

logger = logging.getLogger(__name__)

MAX_SOURCE_CHARACTERS = 60_000
MAX_JOB_CHARACTERS = 20_000
MAX_DIFF_CHANGES = 200

DEFAULT_PROMPT_ID = "keywords"

ALLOWED_CHANGE_ROOTS = {
    "summary",
    "workExperience",
    "education",
    "personalProjects",
    "additional",
}

PROTECTED_TOKENS = {"personalInfo", "years", "company", "institution"}

LIST_FIELDS = (
    "technicalSkills",
    "certificationsTraining",
    "languages",
    "awards",
)


class PromptSizeError(ValueError):
    """Raised when a source input is too large for the LLM context."""


def require_source_size(value: Any, limit: int = MAX_SOURCE_CHARACTERS) -> None:
    """Reject oversized inputs before starting expensive AI work."""
    if value is None:
        return
    size = len(value) if isinstance(value, (str, list, dict)) else len(str(value))
    if size > limit:
        raise PromptSizeError(
            f"Source input too large ({size} > {limit} characters)."
        )


def _language(language: str) -> str:
    return get_language_name(language or "en")


def extract_job_keywords(job_content: str) -> dict[str, Any]:
    """Extract structured keywords from a job description."""
    require_source_size(job_content, MAX_JOB_CHARACTERS)
    prompt = EXTRACT_KEYWORDS_PROMPT.format(job_description=job_content)
    result = generate_structured_output(
        system_prompt=(
            "You are a job description analyst. Extract structured job "
            "requirements. Return ONLY valid JSON matching the requested "
            "schema and never invent details absent from the posting."
        ),
        user_prompt=prompt,
        schema=JobKeywords,
    )
    return normalize_job_keywords(result)


def normalize_job_keywords(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return JobKeywords().model_dump()
    validated = JobKeywords.model_validate(raw)
    return validated.model_dump()


def all_job_keywords(job_keywords: dict[str, Any]) -> list[str]:
    """Flatten every keyword-ish value into one de-duplicated list."""
    values: list[str] = []
    for key in (
        "required_skills",
        "preferred_skills",
        "keywords",
        "key_responsibilities",
        "experience_requirements",
        "education_requirements",
    ):
        items = job_keywords.get(key, [])
        if isinstance(items, list):
            values.extend(str(item) for item in items if item)
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            ordered.append(value)
    return ordered


def generate_skill_target_plan(
    original_resume_data: dict[str, Any],
    job_description: str,
    job_keywords: dict[str, Any],
    language: str = "en",
) -> dict[str, Any]:
    """Ask the LLM for skills worth emphasizing for this job."""
    prompt = SKILL_TARGET_PLAN_PROMPT.format(
        existing_skills=json.dumps(
            (original_resume_data.get("additional") or {}).get(
                "technicalSkills", []
            ),
            ensure_ascii=False,
        ),
        job_keywords=json.dumps(job_keywords, ensure_ascii=False),
        job_description=job_description,
        output_language=_language(language),
        original_resume=json.dumps(original_resume_data, ensure_ascii=False),
    )
    result = generate_structured_output(
        system_prompt=(
            "You are a career coach building a skill target plan for resume "
            "tailoring. Return ONLY valid JSON matching the schema."
        ),
        user_prompt=prompt,
        schema=SkillTargetPlanOutput,
    )
    if not isinstance(result, dict):
        result = SkillTargetPlanOutput.model_validate(result).model_dump()
    return result


def verify_skill_target_plan(
    raw_plan: Any,
    original_resume_data: dict[str, Any],
    job_keywords: dict[str, Any],
    job_description: str,
) -> dict[str, list[dict[str, Any]]]:
    """Keep only targets grounded in the resume or the job description."""
    del job_description  # already used when the plan was generated

    if not isinstance(raw_plan, dict):
        return {"accepted": [], "rejected": []}

    resume_skills = {
        str(skill).strip().casefold()
        for skill in (
            (original_resume_data.get("additional") or {}).get(
                "technicalSkills", []
            )
            or []
        )
        if str(skill).strip()
    }
    jd_skills = {
        keyword.casefold() for keyword in all_job_keywords(job_keywords)
    }

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[str] = set()

    for target in raw_plan.get("target_skills", []) or []:
        if not isinstance(target, dict):
            continue
        skill = str(target.get("skill", "")).strip()
        if not skill:
            continue
        key = skill.casefold()
        if key in seen:
            continue
        seen.add(key)
        if key in resume_skills or key in jd_skills:
            accepted.append(target)
        else:
            rejected.append(target)

    return {"accepted": accepted, "rejected": rejected}


def _skill_target_list(skill_targets: list[dict[str, Any]]) -> list[str]:
    return [
        str(target.get("skill", "")).strip()
        for target in skill_targets
        if isinstance(target, dict) and str(target.get("skill", "")).strip()
    ]


def generate_resume_diffs(
    original_resume: str,
    job_description: str,
    job_keywords: dict[str, Any],
    language: str = "en",
    prompt_id: str = DEFAULT_PROMPT_ID,
    original_resume_data: dict[str, Any] | None = None,
    skill_targets: list[dict[str, Any]] | None = None,
) -> ResumeDiffOutput:
    """Generate targeted, verifiable edits instead of a full rewrite."""
    strategy = DIFF_STRATEGY_INSTRUCTIONS.get(
        prompt_id,
        DIFF_STRATEGY_INSTRUCTIONS[DEFAULT_PROMPT_ID],
    )
    prompt = DIFF_IMPROVE_PROMPT.format(
        strategy_instruction=strategy,
        job_keywords=json.dumps(job_keywords, ensure_ascii=False),
        skill_targets=json.dumps(
            _skill_target_list(skill_targets or []), ensure_ascii=False
        ),
        job_description=job_description,
        output_language=_language(language),
        original_resume=json.dumps(
            original_resume_data
            or normalize_resume_data({"summary": "", "workExperience": []}),
            ensure_ascii=False,
        )
        if original_resume_data
        else original_resume,
    )
    result = generate_structured_output(
        system_prompt=(
            "You are an expert resume editor. Return ONLY valid JSON with the "
            "requested changes. Every 'original' value must be copied exactly "
            "from the resume so it can be verified. Never modify personal "
            "information, dates, companies, institutions, or degrees."
        ),
        user_prompt=prompt,
        schema=ResumeDiffOutput,
    )
    if not isinstance(result, dict):
        result = ResumeDiffOutput.model_validate(result).model_dump()
    return ResumeDiffOutput.model_validate(result)


# ---------------------------------------------------------------------------
# Applying changes
# ---------------------------------------------------------------------------

def _parse_path(path: str) -> list[str | int]:
    tokens: list[str | int] = []
    for part in str(path).split("."):
        match = re.match(r"^([^\[\]]+)((?:\[\d+\])*)$", part.strip())
        if not match:
            raise ValueError(f"Unparsable path: {path}")
        tokens.append(match.group(1))
        tokens.extend(int(idx) for idx in re.findall(r"\[(\d+)\]", match.group(2)))
    return tokens


def _resolve(
    container: Any, tokens: list[str | int]
) -> tuple[Any, str | int] | None:
    current = container
    for token in tokens[:-1]:
        if isinstance(token, int):
            if not isinstance(current, list) or token >= len(current):
                return None
            current = current[token]
        else:
            if not isinstance(current, dict) or token not in current:
                return None
            current = current[token]

    last = tokens[-1]
    if isinstance(last, int):
        if not isinstance(current, list) or last >= len(current):
            return None
    else:
        if not isinstance(current, dict):
            return None
    return current, last


def _read_path(container: Any, path: str) -> Any:
    resolved = _resolve(container, _parse_path(path))
    if resolved is None:
        return None
    parent, key = resolved
    return parent[key]


def _write_path(container: Any, path: str, value: Any) -> bool:
    resolved = _resolve(container, _parse_path(path))
    if resolved is None:
        return False
    parent, key = resolved
    parent[key] = value
    return True


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def _original_matches(current: Any, expected: Any) -> bool:
    if expected is None:
        return True
    if not isinstance(current, str):
        return False
    current_norm = _normalize_text(current)
    expected_norm = _normalize_text(expected)
    if not expected_norm:
        return True
    if not current_norm:
        return False
    return (
        current_norm == expected_norm
        or expected_norm in current_norm
        or current_norm in expected_norm
    )


def _change_allowed(change: ResumeChange) -> bool:
    tokens = _parse_path(change.path)
    root = str(tokens[0])
    if root not in ALLOWED_CHANGE_ROOTS:
        return False
    return not any(str(token) in PROTECTED_TOKENS for token in tokens[1:])


def apply_diffs(
    original: dict[str, Any],
    changes: list[ResumeChange] | list[dict[str, Any]],
    allowed_skill_targets: list[str] | None = None,
) -> tuple[dict[str, Any], list[ResumeChange], list[ResumeChange]]:
    """Apply verified changes to a deep copy of the original resume.

    Returns ``(improved, applied, rejected)``.
    """
    result = copy.deepcopy(original)
    applied: list[ResumeChange] = []
    rejected: list[ResumeChange] = []

    allowed_lower = {
        str(skill).strip().casefold() for skill in (allowed_skill_targets or [])
    }

    for raw_change in changes:
        change = (
            raw_change
            if isinstance(raw_change, ResumeChange)
            else ResumeChange.model_validate(raw_change)
        )
        reason: str | None = None

        try:
            if not _change_allowed(change):
                reason = "path targets protected content"
            else:
                current = _read_path(result, change.path)

                if change.action == "replace":
                    if not isinstance(current, str):
                        reason = "target is not text"
                    elif not _original_matches(current, change.original):
                        reason = "original text does not match the resume"
                    elif not isinstance(change.value, str):
                        reason = "replacement value is not text"
                    else:
                        _write_path(result, change.path, change.value)

                elif change.action == "append":
                    if not isinstance(current, list):
                        reason = "target is not a list"
                    elif not isinstance(change.value, str) or not change.value.strip():
                        reason = "append value is empty"
                    elif any(
                        _normalize_text(item) == _normalize_text(change.value)
                        for item in current
                    ):
                        reason = "value already present"
                    else:
                        current.append(change.value)

                elif change.action == "reorder":
                    if not isinstance(current, list) or not isinstance(
                        change.value, list
                    ):
                        reason = "reorder requires lists"
                    elif {
                        _normalize_text(item) for item in current
                    } != {_normalize_text(item) for item in change.value}:
                        reason = "reorder must preserve every item"
                    else:
                        _write_path(result, change.path, list(change.value))

                elif change.action == "add_skill":
                    if not isinstance(current, list):
                        reason = "target is not a skills list"
                    elif not isinstance(change.value, str) or not change.value.strip():
                        reason = "skill value is empty"
                    elif any(
                        _normalize_text(item) == _normalize_text(change.value)
                        for item in current
                    ):
                        reason = "skill already present"
                    elif allowed_skill_targets is not None and (
                        _normalize_text(change.value) not in allowed_lower
                    ):
                        reason = "skill is not a verified target"
                    else:
                        current.append(change.value.strip())

                else:
                    reason = f"unsupported action: {change.action}"
        except (TypeError, ValueError, IndexError, KeyError) as exc:
            reason = f"could not apply change: {exc}"

        if reason:
            logger.info("Rejected resume change at %s: %s", change.path, reason)
            rejected.append(change)
        else:
            applied.append(change)

    return result, applied, rejected


def verify_diff_result(
    original: dict[str, Any],
    result: dict[str, Any],
    applied_changes: list[ResumeChange],
    job_keywords: dict[str, Any],
) -> list[str]:
    """Warn when applied edits did not stick or dropped source keywords."""
    warnings: list[str] = []

    for change in applied_changes:
        if change.action != "replace":
            continue
        try:
            final_value = _read_path(result, change.path)
        except (ValueError, TypeError):
            final_value = None
        if not isinstance(final_value, str) or _normalize_text(final_value) != _normalize_text(
            change.value
        ):
            warnings.append(
                f"Change at {change.path} was not retained during verification"
            )

    original_text = _normalize_text(json.dumps(original, ensure_ascii=False))
    result_text = _normalize_text(json.dumps(result, ensure_ascii=False))

    dropped: list[str] = []
    for keyword in all_job_keywords(job_keywords)[:40]:
        needle = _normalize_text(keyword)
        if len(needle) < 3:
            continue
        if needle in original_text and needle not in result_text:
            dropped.append(keyword)
    if dropped:
        warnings.append(
            "Keyword(s) removed during tailoring: " + ", ".join(dropped[:5])
        )

    return warnings


# ---------------------------------------------------------------------------
# Full-output fallback (no structured source data)
# ---------------------------------------------------------------------------

def improve_resume(
    original_resume: str,
    job_description: str,
    job_keywords: dict[str, Any],
    language: str = "en",
    prompt_id: str = DEFAULT_PROMPT_ID,
    original_resume_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full-output tailoring used when no structured resume data exists."""
    prompt_id = prompt_id if prompt_id in IMPROVE_RESUME_PROMPTS else DEFAULT_PROMPT_ID
    template = IMPROVE_RESUME_PROMPTS[prompt_id]
    rules = CRITICAL_TRUTHFULNESS_RULES[prompt_id]

    prompt = template.format(
        critical_truthfulness_rules=rules,
        output_language=_language(language),
        job_description=job_description,
        job_keywords=json.dumps(job_keywords, ensure_ascii=False),
        original_resume=json.dumps(
            original_resume_data, ensure_ascii=False
        )
        if original_resume_data
        else original_resume,
        schema=IMPROVE_SCHEMA_EXAMPLE,
    )

    result = generate_structured_output(
        system_prompt=(
            "You are an expert ATS resume writer. Return ONLY the resume JSON "
            "object with every required field. Never invent experience, "
            "employers, metrics, dates, or skills."
        ),
        user_prompt=prompt,
        schema=ResumeData,
    )
    if not isinstance(result, dict):
        result = ResumeData.model_validate(result).model_dump()
    return normalize_resume_data(result)


# ---------------------------------------------------------------------------
# Diff calculation + improvement suggestions
# ---------------------------------------------------------------------------

def _record(
    changes: list[ResumeFieldDiff],
    sections: set[str],
    path: str,
    section: str,
    original_value: Any,
    improved_value: Any,
) -> None:
    if len(changes) >= MAX_DIFF_CHANGES:
        return
    if _normalize_text(original_value) == _normalize_text(improved_value):
        return
    sections.add(section)
    if not str(original_value or "").strip():
        change_type = "added"
    elif not str(improved_value or "").strip():
        change_type = "removed"
    else:
        change_type = "modified"
    changes.append(
        ResumeFieldDiff(
            path=path,
            section=section,
            change_type=change_type,  # type: ignore[arg-type]
            original=str(original_value or ""),
            improved=str(improved_value or ""),
        )
    )


def calculate_resume_diff(
    original: dict[str, Any],
    improved: dict[str, Any],
) -> tuple[ResumeDiffSummary, list[ResumeFieldDiff]]:
    """Field-level diff between the source and the tailored resume."""
    changes: list[ResumeFieldDiff] = []
    sections: set[str] = set()

    _record(changes, sections, "summary", "summary",
            original.get("summary"), improved.get("summary"))

    for section_key, fields in (
        ("workExperience", ("title", "company", "years")),
        ("education", ("degree", "institution", "years")),
        ("personalProjects", ("name", "role", "years")),
    ):
        orig_entries = original.get(section_key, []) or []
        new_entries = improved.get(section_key, []) or []
        for idx in range(max(len(orig_entries), len(new_entries))):
            orig_entry = orig_entries[idx] if idx < len(orig_entries) else {}
            new_entry = new_entries[idx] if idx < len(new_entries) else {}
            if not isinstance(orig_entry, dict):
                orig_entry = {}
            if not isinstance(new_entry, dict):
                new_entry = {}
            for field in fields:
                _record(
                    changes,
                    sections,
                    f"{section_key}[{idx}].{field}",
                    section_key,
                    orig_entry.get(field),
                    new_entry.get(field),
                )
            _record_bullets(
                changes,
                sections,
                f"{section_key}[{idx}].description",
                section_key,
                orig_entry.get("description"),
                new_entry.get("description"),
            )

    orig_additional = original.get("additional", {}) or {}
    new_additional = improved.get("additional", {}) or {}
    if isinstance(orig_additional, dict) and isinstance(new_additional, dict):
        for field in LIST_FIELDS:
            _record(
                changes,
                sections,
                f"additional.{field}",
                "additional",
                ", ".join(
                    str(item)
                    for item in (orig_additional.get(field) or [])
                    if item
                ),
                ", ".join(
                    str(item)
                    for item in (new_additional.get(field) or [])
                    if item
                ),
            )

    orig_custom = original.get("customSections", {}) or {}
    new_custom = improved.get("customSections", {}) or {}
    if isinstance(orig_custom, dict) and isinstance(new_custom, dict):
        for key in sorted(set(orig_custom) | set(new_custom)):
            orig_section = orig_custom.get(key) or {}
            new_section = new_custom.get(key) or {}
            if orig_section.get("sectionType") == "text":
                _record(
                    changes,
                    sections,
                    f"customSections.{key}.text",
                    "customSections",
                    orig_section.get("text"),
                    new_section.get("text"),
                )
                continue
            _record_bullets(
                changes,
                sections,
                f"customSections.{key}.items",
                "customSections",
                [
                    item.get("title") or item.get("years") or ""
                    for item in (orig_section.get("items") or [])
                    if isinstance(item, dict)
                ],
                [
                    item.get("title") or item.get("years") or ""
                    for item in (new_section.get("items") or [])
                    if isinstance(item, dict)
                ],
            )

    modified = sum(1 for change in changes if change.change_type == "modified")
    added = sum(1 for change in changes if change.change_type == "added")
    removed = sum(1 for change in changes if change.change_type == "removed")

    summary = ResumeDiffSummary(
        total_changes=len(changes),
        modified=modified,
        added=added,
        removed=removed,
        sections_changed=sorted(sections),
    )
    return summary, changes


def _record_bullets(
    changes: list[ResumeFieldDiff],
    sections: set[str],
    path: str,
    section: str,
    original_bullets: Any,
    improved_bullets: Any,
) -> None:
    orig_list = (
        [str(item) for item in original_bullets]
        if isinstance(original_bullets, list)
        else [str(original_bullets)] if original_bullets else []
    )
    new_list = (
        [str(item) for item in improved_bullets]
        if isinstance(improved_bullets, list)
        else [str(improved_bullets)] if improved_bullets else []
    )
    for idx in range(max(len(orig_list), len(new_list))):
        orig_value = orig_list[idx] if idx < len(orig_list) else ""
        new_value = new_list[idx] if idx < len(new_list) else ""
        _record(
            changes,
            sections,
            f"{path}[{idx}]",
            section,
            orig_value,
            new_value,
        )


SUGGESTION_TEMPLATES = [
    "Mention {keyword} in your professional summary when it matches your experience",
    "Add {keyword} to your skills section if you have hands-on experience with it",
    "Reframe an achievement using the job description's phrasing for {keyword}",
    "Quantify the impact of work involving {keyword}",
    "Mirror the job posting's terminology around {keyword} in your most recent role",
    "Group {keyword} with related tools so ATS parsers pick it up",
]


def generate_improvements(job_keywords: dict[str, Any]) -> list[dict[str, Any]]:
    """Build actionable improvement suggestions from the job keywords."""
    keywords = all_job_keywords(job_keywords)
    improvements: list[dict[str, Any]] = []
    for index, keyword in enumerate(keykeywords(keywords)):
        template = SUGGESTION_TEMPLATES[index % len(SUGGESTION_TEMPLATES)]
        improvements.append(
            {"suggestion": template.format(keyword=keyword), "lineNumber": None}
        )
        if len(improvements) >= 6:
            break
    return improvements


def keykeywords(keywords: list[str]) -> list[str]:
    """De-duplicate keywords preserving order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for keyword in keywords:
        key = keyword.casefold()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(keyword)
    return ordered


PROMPT_IDS = [option["id"] for option in IMPROVE_PROMPT_OPTIONS]


def is_valid_prompt_id(prompt_id: str | None) -> bool:
    return not prompt_id or prompt_id in PROMPT_IDS
