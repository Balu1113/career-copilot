SKILL_CATEGORY_ALIASES = {
    "programming_languages": {
        "programming languages",
        "languages",
        "programming",
        "languages programming",
    },
    "frameworks": {
        "frameworks",
        "framework",
        "libraries",
    },
    "tools_and_technologies": {
        "tools and technologies",
        "tools & technologies",
        "tools",
        "technologies",
        "databases",
        "other",
        "devops",
        "cloud",
    },
    "ai_ml_technologies": {
        "ai ml technologies",
        "ai ml",
        "ai",
        "ml",
        "machine learning",
        "artificial intelligence",
        "ai & ml",
        "ai/ ml",
        "ai/ml",
    },
}


def _clean(value):
    if value is None:
        return ""

    if isinstance(value, list):
        return [
            str(item).strip()
            for item in value
            if item and str(item).strip()
        ]

    if isinstance(value, dict):
        return value

    return str(value).strip()


def _date_range(start_date, end_date, current=False):
    start = _clean(start_date)
    end = "Present" if current else _clean(end_date)

    if start and end:
        return f"{start} - {end}"

    return start or end


def generated_resume_to_text(content):
    """
    Render structured generated resume content as plain text
    so it can be fed into the career analysis agents.
    """
    content = content or {}

    personal = content.get("personal") or {}
    summary = _clean(content.get("summary"))
    skills = content.get("skills") or {}
    experience = content.get("experience") or []
    projects = content.get("projects") or []
    education = content.get("education") or []
    certifications = content.get("certifications") or []
    publications = content.get("publications") or []

    lines = []

    name = _clean(personal.get("name"))
    if name:
        lines.append(name)

    contact_parts = [
        _clean(personal.get("email")),
        _clean(personal.get("phone")),
        _clean(personal.get("location")),
        _clean(personal.get("linkedin")),
        _clean(personal.get("github")),
        _clean(personal.get("website")),
    ]
    contact_parts = [part for part in contact_parts if part]

    if contact_parts:
        lines.append(" | ".join(contact_parts))

    if summary:
        if lines:
            lines.append("")

        lines.append("PROFESSIONAL SUMMARY")
        lines.append(summary)

    if skills:
        if lines:
            lines.append("")

        lines.append("SKILLS")

        for category, items in skills.items():
            cleaned_items = _clean(items)

            if not cleaned_items:
                continue

            lines.append(
                f"{category}: "
                + ", ".join(
                    str(item) for item in cleaned_items
                )
            )

    if experience:
        if lines:
            lines.append("")

        lines.append("EXPERIENCE")

        for entry in experience:
            entry = entry or {}

            role = _clean(entry.get("role"))
            company = _clean(entry.get("company"))
            location = _clean(entry.get("location"))
            dates = _date_range(
                entry.get("start_date"),
                entry.get("end_date"),
                bool(entry.get("current")),
            )

            heading_parts = [
                part
                for part in [
                    " - ".join(
                        part
                        for part in [role, company]
                        if part
                    ),
                    location,
                    dates,
                ]
                if part
            ]

            lines.append(" • ".join(heading_parts))

            for bullet in _clean(entry.get("bullets")):
                lines.append(f"- {bullet}")

            lines.append("")

    if projects:
        if lines and lines[-1] != "":
            lines.append("")

        lines.append("PROJECTS")

        for entry in projects:
            entry = entry or {}

            project_name = _clean(entry.get("name"))
            project_description = _clean(
                entry.get("description")
            )
            technologies = _clean(
                entry.get("technologies")
            )
            bullets = _clean(entry.get("bullets"))

            if project_name:
                lines.append(project_name)

            if project_description:
                lines.append(project_description)

            if technologies:
                lines.append(
                    "Technologies: "
                    + ", ".join(
                        str(item)
                        for item in technologies
                    )
                )

            for bullet in bullets:
                lines.append(f"- {bullet}")

            lines.append("")

    if education:
        if lines and lines[-1] != "":
            lines.append("")

        lines.append("EDUCATION")

        for entry in education:
            entry = entry or {}

            degree = _clean(entry.get("degree"))
            institution = _clean(
                entry.get("institution")
            )
            location = _clean(entry.get("location"))
            dates = _date_range(
                entry.get("start_date"),
                entry.get("end_date"),
            )
            grade = _clean(entry.get("grade"))

            heading_parts = [
                part
                for part in [
                    " - ".join(
                        part
                        for part in [degree, institution]
                        if part
                    ),
                    location,
                    dates,
                ]
                if part
            ]

            lines.append(" • ".join(heading_parts))

            if grade:
                lines.append(f"Grade: {grade}")

            lines.append("")

    if certifications:
        if lines and lines[-1] != "":
            lines.append("")

        lines.append("CERTIFICATIONS")

        for entry in certifications:
            entry = entry or {}

            cert_name = _clean(entry.get("name"))
            issuer = _clean(entry.get("issuer"))
            date = _clean(entry.get("date"))

            parts = [
                part
                for part in [
                    cert_name,
                    issuer,
                    date,
                ]
                if part
            ]

            lines.append(" • ".join(parts))

        lines.append("")

    if publications:
        if lines and lines[-1] != "":
            lines.append("")

        lines.append("PUBLICATIONS")

        for entry in publications:
            entry = entry or {}

            parts = [
                part
                for part in [
                    _clean(entry.get("title")),
                    _clean(entry.get("authors")),
                    _clean(entry.get("venue")),
                    _clean(entry.get("date")),
                ]
                if part
            ]

            lines.append(" • ".join(parts))

        lines.append("")

    return "\n".join(lines).strip()


def _skills_for_category(skills, alias_key):
    aliases = SKILL_CATEGORY_ALIASES[alias_key]
    values = []

    for category, items in (skills or {}).items():
        normalized = str(category).strip().lower()

        if normalized not in aliases:
            continue

        for item in _clean(items):
            if item not in values:
                values.append(item)

    return values


def generated_resume_to_intelligence(content):
    """
    Map generated resume content into the ResumeIntelligence
    structure consumed by the career analysis workflow.
    """
    content = content or {}

    skills = content.get("skills") or {}

    all_skills = []
    for items in skills.values():
        for item in _clean(items):
            if item not in all_skills:
                all_skills.append(item)

    projects = []
    for entry in content.get("projects") or []:
        entry = entry or {}

        description = _clean(entry.get("description"))
        bullets = _clean(entry.get("bullets"))
        description_lines = bullets or (
            [description] if description else []
        )

        projects.append(
            {
                "name": _clean(entry.get("name")),
                "description": description_lines,
                "technologies": _clean(
                    entry.get("technologies")
                ),
            }
        )

    experience = []
    for entry in content.get("experience") or []:
        entry = entry or {}

        experience.append(
            {
                "company": _clean(entry.get("company")),
                "role": _clean(entry.get("role")),
                "description": _clean(
                    entry.get("bullets")
                ),
                "technologies": [],
            }
        )

    education = []
    for entry in content.get("education") or []:
        entry = entry or {}

        education.append(
            {
                "institution": _clean(
                    entry.get("institution")
                ),
                "degree": _clean(entry.get("degree")),
                "dates": _date_range(
                    entry.get("start_date"),
                    entry.get("end_date"),
                ),
            }
        )

    certifications = []
    for entry in content.get("certifications") or []:
        entry = entry or {}

        certifications.append(
            {
                "name": _clean(entry.get("name")),
                "issuer": _clean(entry.get("issuer")),
            }
        )

    return {
        "professional_summary": _clean(
            content.get("summary")
        ),
        "skills": all_skills,
        "programming_languages": _skills_for_category(
            skills, "programming_languages"
        ),
        "frameworks": _skills_for_category(
            skills, "frameworks"
        ),
        "tools_and_technologies": _skills_for_category(
            skills, "tools_and_technologies"
        ),
        "ai_ml_technologies": _skills_for_category(
            skills, "ai_ml_technologies"
        ),
        "projects": projects,
        "experience": experience,
        "education": education,
        "certifications": certifications,
    }
