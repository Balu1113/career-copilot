"""
Built-in, ATS-friendly resume templates.

Every account gets a copy of these templates the first time the
template list is loaded. They are ordinary ``ResumeTemplate`` rows
(except ``is_builtin=True`` and no ``sample_file``), so selection,
generation and rendering keep working unchanged.

``template_data`` follows the exact shape produced by
``services.template_analyzer`` so ``docx_renderer`` can consume it:

    page, typography, header, section_heading, body, layout, sections

The extra ``preview`` block is only used by the frontend to draw a
thumbnail / full-screen preview of the design. Each template has its
own header treatment, accent colour, heading rule and skill list
style so the picker does not show six identical thumbnails.
"""

from django.utils import timezone

from ..models import ResumeTemplate


def _page(margin_top, margin_bottom, margin_side):
    return {
        "size": "A4",
        "width_inches": 8.27,
        "height_inches": 11.69,
        "margin_top": margin_top,
        "margin_bottom": margin_bottom,
        "margin_left": margin_side,
        "margin_right": margin_side,
    }


def _template(
    slug,
    name,
    description,
    ats_score,
    font,
    body_size,
    header_size,
    heading_size,
    margins,
    accent,
    accent_soft,
    header_style,
    heading_style,
    skill_style,
    header_align,
    density,
    sections,
):
    return {
        "slug": slug,
        "name": name,
        "description": description,
        "ats_score": ats_score,
        "template_data": {
            "file_type": "builtin",
            "page": _page(*margins),
            "typography": {
                "body_size": body_size,
                "font": font,
                "header_size": header_size,
            },
            "header": {
                "font": font,
                "font_size": header_size,
                "alignment": header_align,
            },
            "section_heading": {
                "font": font,
                "font_size": heading_size,
                "alignment": "left",
            },
            "body": {
                "font": font,
                "font_size": body_size,
                "alignment": "left",
            },
            "layout": {"columns": 1, "page_count": 1},
            "sections": sections,
            "preview": {
                "accent": accent,
                "accent_soft": accent_soft,
                "header_style": header_style,
                "heading_style": heading_style,
                "skill_style": skill_style,
                "font_css": f"'{font}', 'Segoe UI', sans-serif",
                "font_label": font,
                "header_align": header_align,
                "density": density,
            },
        },
    }


# All layouts are single column on purpose: two-column designs are
# parsed badly by most Applicant Tracking Systems.
BUILTIN_TEMPLATES = [
    _template(
        slug="classic-linked",
        name="Classic Linked",
        description=(
            "Clean Arial resume inspired by a traditional academic layout: "
            "a centred name, icon-led contact links, and bold underlined "
            "section labels with full-width black rules."
        ),
        ats_score=98,
        font="Arial",
        body_size=10.5,
        header_size=18.0,
        heading_size=11.0,
        margins=(0.32, 0.4, 0.57),
        accent="#000000",
        accent_soft="#ffffff",
        header_style="reference",
        heading_style="reference",
        skill_style="reference",
        header_align="center",
        density="compact",
        sections=[
            "education",
            "projects",
            "skills",
            "certifications",
            "experience",
        ],
    ),
    _template(
        slug="ats-classic",
        name="Classic ATS",
        description=(
            "Traditional serif resume: centred name, twin charcoal "
            "rules and a dot-separated skill line. The most "
            "conservative option for applicant tracking systems."
        ),
        ats_score=98,
        font="Times New Roman",
        body_size=11.0,
        header_size=24.0,
        heading_size=13.0,
        margins=(0.75, 0.7, 0.8),
        accent="#1f2937",
        accent_soft="#f3f4f6",
        header_style="centered",
        heading_style="rule",
        skill_style="pipes",
        header_align="center",
        density="comfortable",
        sections=[
            "summary",
            "skills",
            "experience",
            "projects",
            "education",
            "certifications",
        ],
    ),
    _template(
        slug="ats-modern",
        name="Modern ATS",
        description=(
            "Indigo accent bar beside the name, indigo section "
            "markers and pill-shaped skill tags. Fresh on screen "
            "while staying fully machine readable."
        ),
        ats_score=97,
        font="Calibri",
        body_size=11.0,
        header_size=25.0,
        heading_size=13.5,
        margins=(0.7, 0.7, 0.75),
        accent="#4f46e5",
        accent_soft="#eef2ff",
        header_style="accent",
        heading_style="bar",
        skill_style="chips",
        header_align="left",
        density="comfortable",
        sections=[
            "summary",
            "skills",
            "experience",
            "projects",
            "education",
            "certifications",
        ],
    ),
    _template(
        slug="ats-minimal",
        name="Minimal ATS",
        description=(
            "Ultra-clean layout: tracked uppercase name, hairline "
            "grey rule, plain text skills and a lot of whitespace. "
            "Nothing between your content and the parser."
        ),
        ats_score=99,
        font="Arial",
        body_size=10.5,
        header_size=19.0,
        heading_size=10.5,
        margins=(0.85, 0.75, 0.85),
        accent="#111827",
        accent_soft="#f9fafb",
        header_style="minimal",
        heading_style="caps",
        skill_style="pipes",
        header_align="left",
        density="airy",
        sections=[
            "summary",
            "skills",
            "experience",
            "education",
            "certifications",
        ],
    ),
    _template(
        slug="ats-compact",
        name="Compact ATS",
        description=(
            "Burnt-orange banner across the top with a subtle "
            "diagonal weave, tight spacing and small skill tags. "
            "Fits an extra third of content on one page."
        ),
        ats_score=95,
        font="Segoe UI",
        body_size=10.0,
        header_size=21.0,
        heading_size=11.5,
        margins=(0.5, 0.5, 0.6),
        accent="#c2410c",
        accent_soft="#fff7ed",
        header_style="band",
        heading_style="underline",
        skill_style="chips",
        header_align="left",
        density="compact",
        sections=[
            "summary",
            "skills",
            "experience",
            "projects",
            "education",
            "certifications",
            "publications",
        ],
    ),
    _template(
        slug="ats-executive",
        name="Executive ATS",
        description=(
            "Navy serif with a split header — name and role on the "
            "left, contact details aligned right — and generous "
            "margins for leadership and consulting applications."
        ),
        ats_score=94,
        font="Cambria",
        body_size=11.0,
        header_size=27.0,
        heading_size=13.5,
        margins=(0.85, 0.7, 0.85),
        accent="#1e3a5f",
        accent_soft="#eff6ff",
        header_style="split",
        heading_style="rule",
        skill_style="pipes",
        header_align="left",
        density="comfortable",
        sections=[
            "summary",
            "experience",
            "education",
            "skills",
            "certifications",
            "publications",
        ],
    ),
    _template(
        slug="ats-technical",
        name="Technical ATS",
        description=(
            "Teal bordered name plate, teal section markers and a "
            "three-column grid of skill boxes. Built for engineering "
            "and data resumes where the skill list must scan fast."
        ),
        ats_score=96,
        font="Arial",
        body_size=10.5,
        header_size=23.0,
        heading_size=12.0,
        margins=(0.6, 0.6, 0.65),
        accent="#0f766e",
        accent_soft="#f0fdfa",
        header_style="boxed",
        heading_style="bar",
        skill_style="grid",
        header_align="left",
        density="compact",
        sections=[
            "skills",
            "summary",
            "experience",
            "projects",
            "education",
            "certifications",
        ],
    ),
]


def ensure_builtin_templates(user):
    """
    Create the missing built-in templates for ``user`` and refresh
    any whose design spec has changed since they were created.

    Idempotent: two queries per call, then nothing to do.
    """
    if user is None or not user.is_authenticated:
        return

    rows = {
        row.slug: row
        for row in ResumeTemplate.objects.filter(
            user=user,
            is_builtin=True,
        )
    }

    to_create = []
    to_update = []

    for spec in BUILTIN_TEMPLATES:
        row = rows.get(spec["slug"])

        if row is None:
            to_create.append(
                ResumeTemplate(
                    user=user,
                    slug=spec["slug"],
                    name=spec["name"],
                    description=spec["description"],
                    is_builtin=True,
                    ats_score=spec["ats_score"],
                    file_type="builtin",
                    template_data=spec["template_data"],
                )
            )
            continue

        if (
            row.name != spec["name"]
            or row.description != spec["description"]
            or row.ats_score != spec["ats_score"]
            or row.template_data != spec["template_data"]
        ):
            row.name = spec["name"]
            row.description = spec["description"]
            row.ats_score = spec["ats_score"]
            row.template_data = spec["template_data"]
            row.updated_at = timezone.now()
            to_update.append(row)

    if to_create:
        ResumeTemplate.objects.bulk_create(to_create)

    if to_update:
        ResumeTemplate.objects.bulk_update(
            to_update,
            [
                "name",
                "description",
                "ats_score",
                "template_data",
                "updated_at",
            ],
        )
