from typing import Any

GENERATED_RESUME_TYPES = {"generated", "builder", "resume_builder"}
UPLOADED_RESUME_TYPES = {"uploaded", "resume", "upload"}


def _flatten_to_text(value: Any, label: str = "") -> str:
    """Render nested resume content (dicts/lists) as readable text."""
    if value is None:
        return ""

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return ""
        return f"{label}: {text}" if label else text

    if isinstance(value, dict):
        parts = [
            _flatten_to_text(v, str(k))
            for k, v in value.items()
        ]
        return "\n".join(part for part in parts if part)

    if isinstance(value, list):
        parts = [_flatten_to_text(item, label) for item in value]
        return "\n".join(part for part in parts if part)

    text = str(value).strip()
    if not text:
        return ""
    return f"{label}: {text}" if label else text


def _intelligence_to_dict(intelligence) -> dict[str, Any]:
    fields = [
        "professional_summary",
        "skills",
        "programming_languages",
        "frameworks",
        "tools_and_technologies",
        "ai_ml_technologies",
        "projects",
        "experience",
        "education",
        "certifications",
    ]
    return {
        field: getattr(intelligence, field)
        for field in fields
        if hasattr(intelligence, field)
    }


def hydrate_resume_payload(
    resume: dict[str, Any],
    user=None,
) -> dict[str, Any]:
    """
    Fill in resume content and intelligence from the database.

    The frontend only sends ``{id, type}`` when calling the application
    agent, but the workflow needs the actual resume text. Explicit values
    already present in the payload always win over database values.
    """
    hydrated = dict(resume)

    existing_text = hydrated.get("extracted_text")
    if isinstance(existing_text, str) and existing_text.strip():
        if hydrated.get("resume_intelligence"):
            return hydrated
    else:
        existing_text = ""

    raw_id = hydrated.get("id")
    if raw_id in (None, ""):
        if not existing_text:
            raise ValueError(
                "Resume content is required: provide content or a resume id."
            )
        return hydrated

    try:
        resume_pk = int(raw_id)
    except (TypeError, ValueError):
        if not existing_text:
            raise ValueError(
                f"Invalid resume id: {raw_id!r}."
            ) from None
        return hydrated

    resume_type = str(hydrated.get("type") or "uploaded").lower()

    if resume_type in GENERATED_RESUME_TYPES:
        from resume_builder.models import GeneratedResume

        queryset = GeneratedResume.objects.all()
        if user is not None:
            queryset = queryset.filter(user=user)
        generated = queryset.filter(pk=resume_pk).first()

        if generated is None:
            if not existing_text:
                raise ValueError("Selected resume was not found.")
            return hydrated

        text = _flatten_to_text(generated.content) or ""
        if not text.strip():
            text = "\n".join(
                part
                for part in [
                    generated.title or "",
                    generated.job_description or "",
                ]
                if part
            )

        hydrated.setdefault("title", generated.title)
        hydrated["extracted_text"] = existing_text or text
        return hydrated

    from resumes.models import Resume, ResumeIntelligence

    queryset = Resume.objects.all()
    if user is not None:
        queryset = queryset.filter(user=user)
    uploaded = queryset.filter(pk=resume_pk).first()

    if uploaded is None:
        if not existing_text:
            raise ValueError("Selected resume was not found.")
        return hydrated

    text = existing_text or (
        uploaded.extracted_text or uploaded.original_markdown or ""
    ).strip()

    if not text and uploaded.processed_data:
        text = _flatten_to_text(uploaded.processed_data)

    if not text and not hydrated.get("resume_intelligence"):
        raise ValueError(
            "The selected resume has no extractable text yet. "
            "Re-upload it or wait for processing to finish."
        )

    hydrated["extracted_text"] = text

    if not hydrated.get("resume_intelligence"):
        intelligence = ResumeIntelligence.objects.filter(
            resume=uploaded
        ).first()
        if intelligence is not None:
            hydrated["resume_intelligence"] = _intelligence_to_dict(
                intelligence
            )

    return hydrated
