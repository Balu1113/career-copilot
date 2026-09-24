import re


def normalize_skill(value):
    if not isinstance(value, str):
        return ""

    value = value.lower().strip()

    value = re.sub(
        r"[\-_]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value


def skill_matches(
    text,
    skill,
):
    """
    Determine whether text refers to a skill.

    Handles:
    - exact matches
    - singular/plural forms
    - common punctuation variations
    """

    if not isinstance(text, str):
        return False

    if not isinstance(skill, str):
        return False

    text_normalized = normalize_skill(text)
    skill_normalized = normalize_skill(skill)

    if not text_normalized or not skill_normalized:
        return False

    # Exact phrase (word-boundary match to prevent "ai" matching inside "azure ai search")
    if re.search(
        r"(?<!\w)" + re.escape(skill_normalized) + r"(?!\w)",
        text_normalized,
    ):
        return True

    # Singular/plural handling
    if skill_normalized.endswith("s"):
        singular = skill_normalized[:-1]

        if singular and re.search(
            r"(?<!\w)"
            + re.escape(singular)
            + r"(?!\w)",
            text_normalized,
        ):
            return True

    # Common CI/CD representation
    ci_variants = {
        "continuous integration": [
            "ci",
            "ci cd",
            "ci/cd",
            "continuous integration",
        ],
        "continuous integration and deployment": [
            "ci cd",
            "ci/cd",
            "continuous integration and deployment",
        ],
    }

    variants = ci_variants.get(
        skill_normalized,
        [],
    )

    for variant in variants:
        if re.search(
            r"(?<!\w)" + re.escape(variant) + r"(?!\w)",
            text_normalized,
        ):
            return True

    return False