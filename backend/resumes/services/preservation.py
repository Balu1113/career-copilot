"""Safety nets that keep AI-tailored resumes grounded in the source resume.

Ported from the original resume management endpoints: personal info, dates,
skills and custom sections must survive any LLM rewrite unchanged.
"""

from __future__ import annotations

import copy
import json
import logging
import unicodedata
from typing import Any

from .resume_json import has_month

logger = logging.getLogger(__name__)

LIST_FIELDS = (
    "technicalSkills",
    "certificationsTraining",
    "languages",
    "awards",
)

ENTRY_SECTIONS = ("workExperience", "education", "personalProjects")


def _normalize_personal_info_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value).strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def preserve_personal_info(
    original_data: dict[str, Any] | None,
    improved_data: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Preserve personal info from original, return warnings if unable."""
    warnings: list[str] = []

    if not original_data:
        warnings.append(
            "Original resume data unavailable - personal info may be AI-generated"
        )
        return improved_data, warnings

    original_info = original_data.get("personalInfo")
    if not isinstance(original_info, dict):
        warnings.append("Original personal info missing or invalid")
        return improved_data, warnings

    # SVC-001: Use deep copy to prevent any mutation of original data
    result = copy.deepcopy(improved_data)
    result["personalInfo"] = copy.deepcopy(original_info)
    return result, warnings


def restore_original_dates(
    original_data: dict[str, Any] | None,
    improved_data: dict[str, Any],
) -> dict[str, Any]:
    """Restore original date/years values that the LLM may have truncated."""
    if not original_data:
        return improved_data

    result = copy.deepcopy(improved_data)

    for section_key in ENTRY_SECTIONS:
        orig_entries = original_data.get(section_key, [])
        result_entries = result.get(section_key, [])
        if not isinstance(orig_entries, list) or not isinstance(
            result_entries, list
        ):
            continue
        for idx, orig_entry in enumerate(orig_entries):
            if idx >= len(result_entries):
                break
            if not isinstance(orig_entry, dict) or not isinstance(
                result_entries[idx], dict
            ):
                continue
            orig_years = orig_entry.get("years", "")
            result_years = result_entries[idx].get("years", "")
            if (
                isinstance(orig_years, str)
                and isinstance(result_years, str)
                and orig_years
                and orig_years != result_years
                and has_month(orig_years)
                and not has_month(result_years)
            ):
                logger.info(
                    "Restoring date in %s[%d]: %r -> %r",
                    section_key,
                    idx,
                    result_years,
                    orig_years,
                )
                result_entries[idx]["years"] = orig_years

    # Custom sections (itemList)
    orig_custom = original_data.get("customSections", {})
    result_custom = result.get("customSections", {})
    if isinstance(orig_custom, dict) and isinstance(result_custom, dict):
        for section_key, orig_section in orig_custom.items():
            if not isinstance(orig_section, dict):
                continue
            result_section = result_custom.get(section_key)
            if not isinstance(result_section, dict):
                continue
            if orig_section.get("sectionType") != "itemList":
                continue
            orig_items = orig_section.get("items", [])
            result_items = result_section.get("items", [])
            if not isinstance(orig_items, list) or not isinstance(
                result_items, list
            ):
                continue
            for idx, orig_item in enumerate(orig_items):
                if idx >= len(result_items):
                    break
                if not isinstance(orig_item, dict) or not isinstance(
                    result_items[idx], dict
                ):
                    continue
                orig_years = orig_item.get("years", "")
                result_years = result_items[idx].get("years", "")
                if (
                    isinstance(orig_years, str)
                    and isinstance(result_years, str)
                    and orig_years
                    and orig_years != result_years
                    and has_month(orig_years)
                    and not has_month(result_years)
                ):
                    result_items[idx]["years"] = orig_years

    return result


def preserve_original_skills(
    original_data: dict[str, Any] | None,
    improved_data: dict[str, Any],
) -> dict[str, Any]:
    """Restore any skills, certs, languages, or awards dropped by the LLM.

    This is a hard safety net: regardless of what the LLM returns, no
    original item from these lists is ever lost. Dropped items are
    appended at the end of the improved list.
    """
    if not original_data:
        return improved_data

    result = copy.deepcopy(improved_data)

    orig_additional = original_data.get("additional", {})
    if not isinstance(orig_additional, dict):
        return result
    result_additional = result.setdefault("additional", {})
    if not isinstance(result_additional, dict):
        result_additional = {}
        result["additional"] = result_additional

    for field in LIST_FIELDS:
        orig_items = orig_additional.get(field, [])
        if not isinstance(orig_items, list) or not orig_items:
            continue
        current_items = result_additional.get(field, [])
        if not isinstance(current_items, list):
            current_items = []

        # Build a case-insensitive index of what the LLM kept
        current_lower = {
            item.casefold() for item in current_items if isinstance(item, str)
        }

        # Append any originals that were dropped
        restored = 0
        for item in orig_items:
            if isinstance(item, str) and item.casefold() not in current_lower:
                current_items.append(item)
                current_lower.add(item.casefold())
                restored += 1

        if restored:
            logger.info("Restored %d dropped items in additional.%s", restored, field)
        result_additional[field] = current_items

    return result


def protect_custom_sections(
    original_data: dict[str, Any] | None,
    improved_data: dict[str, Any],
) -> dict[str, Any]:
    """Protect custom sections from LLM hallucination.

    - If an item originally had description: [], revert any fabricated descriptions.
    - If the LLM added items that weren't in the original, remove them.
    - If the LLM removed a whole section, restore it.
    """
    if not original_data:
        return improved_data

    orig_custom = original_data.get("customSections")
    if not isinstance(orig_custom, dict) or not orig_custom:
        return improved_data

    result = copy.deepcopy(improved_data)
    result_custom = result.get("customSections")
    if not isinstance(result_custom, dict):
        result_custom = {}
        result["customSections"] = result_custom

    for section_key, orig_section in orig_custom.items():
        if not isinstance(orig_section, dict):
            continue
        result_section = result_custom.get(section_key)
        if not isinstance(result_section, dict):
            # Section was removed by LLM - restore original
            result_custom[section_key] = copy.deepcopy(orig_section)
            logger.info("Restored missing custom section: %s", section_key)
            continue

        section_type = orig_section.get("sectionType", "")
        if section_type == "itemList":
            orig_items = orig_section.get("items", [])
            result_items = result_section.get("items", [])
            if not isinstance(orig_items, list):
                continue
            if not isinstance(result_items, list):
                result_items = []

            # Trim any items the LLM added beyond the original count
            if len(result_items) > len(orig_items):
                logger.info(
                    "Trimming %d hallucinated items from customSections.%s",
                    len(result_items) - len(orig_items),
                    section_key,
                )
                result_items = result_items[: len(orig_items)]

            # Revert fabricated descriptions on items that had empty descriptions
            for idx, orig_item in enumerate(orig_items):
                if idx >= len(result_items):
                    break
                if not isinstance(orig_item, dict) or not isinstance(
                    result_items[idx], dict
                ):
                    continue
                orig_desc = orig_item.get("description")
                if isinstance(orig_desc, list) and len(orig_desc) == 0:
                    result_desc = result_items[idx].get("description")
                    if isinstance(result_desc, list) and len(result_desc) > 0:
                        logger.info(
                            "Reverted fabricated description on "
                            "customSections.%s.items[%d]",
                            section_key,
                            idx,
                        )
                        result_items[idx]["description"] = []

            result_section["items"] = result_items
        elif section_type == "text":
            # Text sections are rewritten in place; nothing structural to fix.
            pass

    result["customSections"] = result_custom
    return result


def _restore_missing_entries(
    original_data: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    """Re-add whole entries the LLM dropped (never lose source content)."""
    for section_key in ENTRY_SECTIONS:
        orig_entries = original_data.get(section_key, [])
        result_entries = result.get(section_key, [])
        if not isinstance(orig_entries, list) or not isinstance(
            result_entries, list
        ):
            continue
        if len(result_entries) >= len(orig_entries):
            continue
        logger.warning(
            "Restoring %d dropped entr%s in %s",
            len(orig_entries) - len(result_entries),
            "y" if len(orig_entries) - len(result_entries) == 1 else "ies",
            section_key,
        )
        result[section_key] = result_entries + copy.deepcopy(
            orig_entries[len(result_entries) :]
        )
    return result


def _trim_added_rows(
    original_data: dict[str, Any],
    result: dict[str, Any],
    *,
    allow_appended_rows: bool,
) -> dict[str, Any]:
    """Trim rows/entries added beyond what the flow explicitly allowed."""
    for section_key in ENTRY_SECTIONS:
        orig_entries = original_data.get(section_key, [])
        result_entries = result.get(section_key, [])
        if not isinstance(orig_entries, list) or not isinstance(
            result_entries, list
        ):
            continue

        extra = len(result_entries) - len(orig_entries)
        if extra > 0:
            # New entries are never allowed (append actions only add bullets).
            result[section_key] = result_entries[: len(orig_entries)]
            result_entries = result[section_key]

        if not allow_appended_rows:
            for idx, orig_entry in enumerate(orig_entries):
                if idx >= len(result_entries):
                    break
                if not isinstance(orig_entry, dict) or not isinstance(
                    result_entries[idx], dict
                ):
                    continue
                orig_desc = orig_entry.get("description")
                if isinstance(orig_desc, list):
                    cur_desc = result_entries[idx].get("description")
                    if isinstance(cur_desc, list) and len(cur_desc) > len(
                        orig_desc
                    ):
                        result_entries[idx]["description"] = cur_desc[
                            : len(orig_desc)
                        ]
                        styles = result_entries[idx].get("descriptionStyles")
                        if isinstance(styles, list) and len(styles) > len(
                            orig_desc
                        ):
                            result_entries[idx]["descriptionStyles"] = styles[
                                : len(orig_desc)
                            ]

    return result


def validate_confirmed_resume(
    original_data: dict[str, Any],
    improved_data: dict[str, Any],
    *,
    allow_appended_rows: bool = False,
) -> list[str]:
    """Return preservation violations (empty list when the payload is valid)."""
    violations: list[str] = []

    orig_info = original_data.get("personalInfo")
    new_info = improved_data.get("personalInfo")
    if not isinstance(orig_info, dict) or not isinstance(new_info, dict):
        violations.append("personalInfo missing")
    else:
        fields = set(orig_info.keys()) | set(new_info.keys())
        changed = [
            field
            for field in sorted(fields)
            if _normalize_personal_info_value(orig_info.get(field))
            != _normalize_personal_info_value(new_info.get(field))
        ]
        if changed:
            violations.append(
                "personalInfo changed: " + ", ".join(changed)
            )

    for section_key in ENTRY_SECTIONS:
        orig_entries = original_data.get(section_key, [])
        result_entries = improved_data.get(section_key, [])
        if not isinstance(orig_entries, list) or not isinstance(
            result_entries, list
        ):
            violations.append(f"{section_key} is not a list")
            continue

        if len(result_entries) > len(orig_entries):
            violations.append(
                f"{section_key} gained {len(result_entries) - len(orig_entries)} "
                "entry(ies)"
            )
        elif len(result_entries) < len(orig_entries):
            violations.append(
                f"{section_key} lost {len(orig_entries) - len(result_entries)} "
                "entry(ies)"
            )

        for idx, orig_entry in enumerate(orig_entries):
            if idx >= len(result_entries):
                break
            if not isinstance(orig_entry, dict) or not isinstance(
                result_entries[idx], dict
            ):
                continue
            orig_years = orig_entry.get("years", "")
            new_years = result_entries[idx].get("years", "")
            if (
                isinstance(orig_years, str)
                and isinstance(new_years, str)
                and orig_years
                and new_years
                and orig_years != new_years
                and has_month(orig_years)
                and not has_month(new_years)
            ):
                violations.append(
                    f"{section_key}[{idx}].years lost month precision"
                )
            if not allow_appended_rows:
                orig_desc = orig_entry.get("description")
                new_desc = result_entries[idx].get("description")
                if (
                    isinstance(orig_desc, list)
                    and isinstance(new_desc, list)
                    and len(new_desc) > len(orig_desc)
                ):
                    violations.append(
                        f"{section_key}[{idx}].description gained rows"
                    )

        del max_rows

    orig_additional = original_data.get("additional", {})
    new_additional = improved_data.get("additional", {})
    if isinstance(orig_additional, dict) and isinstance(new_additional, dict):
        for field in LIST_FIELDS:
            orig_items = orig_additional.get(field, [])
            new_items = new_additional.get(field, [])
            if not isinstance(orig_items, list) or not isinstance(
                new_items, list
            ):
                violations.append(f"additional.{field} is not a list")
                continue
            new_lower = {
                item.casefold() for item in new_items if isinstance(item, str)
            }
            missing = [
                item
                for item in orig_items
                if isinstance(item, str) and item.casefold() not in new_lower
            ]
            if missing:
                violations.append(
                    f"additional.{field} lost {len(missing)} item(s)"
                )

    orig_custom = original_data.get("customSections", {})
    new_custom = improved_data.get("customSections", {})
    if isinstance(orig_custom, dict) and isinstance(new_custom, dict):
        for section_key, orig_section in orig_custom.items():
            new_section = new_custom.get(section_key)
            if new_section is None:
                violations.append(f"customSections.{section_key} removed")
                continue
            if not isinstance(orig_section, dict) or not isinstance(
                new_section, dict
            ):
                continue
            if orig_section.get("sectionType") != "itemList":
                continue
            orig_items = orig_section.get("items", [])
            new_items = new_section.get("items", [])
            if not isinstance(orig_items, list) or not isinstance(
                new_items, list
            ):
                continue
            if len(new_items) > len(orig_items):
                violations.append(
                    f"customSections.{section_key} gained items"
                )
            elif len(new_items) < len(orig_items):
                violations.append(
                    f"customSections.{section_key} lost items"
                )

    return violations


def grounding_review_warnings(
    original_data: dict[str, Any] | None,
    improved_data: dict[str, Any],
) -> list[str]:
    """Warn about content in the tailored resume that the source never had."""
    if not original_data:
        return [
            "Original resume data unavailable - grounding review skipped"
        ]

    warnings: list[str] = []

    for section_key, field in (
        ("workExperience", "company"),
        ("workExperience", "title"),
        ("education", "institution"),
        ("education", "degree"),
        ("personalProjects", "name"),
    ):
        orig_values = {
            str((entry or {}).get(field, "")).strip().casefold()
            for entry in original_data.get(section_key, [])
            if isinstance(entry, dict)
        }
        orig_values.discard("")
        new_entries = improved_data.get(section_key, [])
        if not isinstance(new_entries, list):
            continue
        added = {
            str((entry or {}).get(field, "")).strip()
            for entry in new_entries
            if isinstance(entry, dict)
            and str((entry or {}).get(field, "")).strip().casefold()
            not in orig_values
            and str((entry or {}).get(field, "")).strip()
        }
        if added:
            warnings.append(
                "GROUNDING: "
                + ", ".join(sorted(added)[:3])
                + f" added to {section_key} but not present in the source resume"
            )

    orig_custom = original_data.get("customSections", {})
    new_custom = improved_data.get("customSections", {})
    if isinstance(orig_custom, dict) and isinstance(new_custom, dict):
        new_sections = set(new_custom) - set(orig_custom)
        if new_sections:
            warnings.append(
                "GROUNDING: new custom section(s) "
                + ", ".join(sorted(new_sections))
                + " not present in the source resume"
            )

    return warnings


def finalize_ai_resume(
    original_data: dict[str, Any],
    improved_data: dict[str, Any],
    *,
    allow_review_claims: bool = True,
    allow_appended_rows: bool = False,
) -> dict[str, Any]:
    """Apply every safety net, then enforce preservation invariants.

    Raises ``ValueError`` when the tailored payload still violates source
    preservation after repair.
    """
    if not original_data:
        return improved_data

    result = copy.deepcopy(improved_data)

    result, _warnings = preserve_personal_info(original_data, result)
    result = restore_original_dates(original_data, result)
    result = preserve_original_skills(original_data, result)
    result = protect_custom_sections(original_data, result)
    result = _restore_missing_entries(original_data, result)

    if allow_review_claims:
        result = _trim_added_rows(
            original_data,
            result,
            allow_appended_rows=allow_appended_rows,
        )

    violations = validate_confirmed_resume(
        original_data,
        result,
        allow_appended_rows=allow_appended_rows,
    )
    if violations:
        raise ValueError(
            "source preservation failed: " + ", ".join(violations)
        )

    return result


def validate_confirm_payload(
    original_data: dict[str, Any] | None,
    improved_data: dict[str, Any],
    *,
    allow_appended_rows: bool = False,
) -> None:
    """Validate a confirmed preview payload; raise ``ValueError`` on mismatch."""
    if not original_data:
        logger.warning(
            "Skipping confirm payload validation; structured resume data unavailable."
        )
        return

    original_info = original_data.get("personalInfo")
    improved_info = improved_data.get("personalInfo")
    # JSON-008: Explicit null checks with clear error messages
    if original_info is None:
        raise ValueError("Original resume missing personalInfo")
    if improved_info is None:
        raise ValueError("Improved resume missing personalInfo")
    if not isinstance(original_info, dict):
        raise ValueError(
            f"Original personalInfo is not a dict: {type(original_info).__name__}"
        )
    if not isinstance(improved_info, dict):
        raise ValueError(
            f"Improved personalInfo is not a dict: {type(improved_info).__name__}"
        )
    fields = set(original_info.keys()) | set(improved_info.keys())
    mismatches = [
        field
        for field in sorted(fields)
        if _normalize_personal_info_value(original_info.get(field))
        != _normalize_personal_info_value(improved_info.get(field))
    ]
    if mismatches:
        raise ValueError(f"personalInfo fields changed: {', '.join(mismatches)}")

    preservation_violations = validate_confirmed_resume(
        original_data, improved_data, allow_appended_rows=allow_appended_rows
    )
    if preservation_violations:
        raise ValueError(
            "source preservation failed: " + ", ".join(preservation_violations)
        )
