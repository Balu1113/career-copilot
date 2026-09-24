from pathlib import Path

from django.conf import settings
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt


DEFAULT_FONT = "Times New Roman"


# -------------------------------------------------------------------
# TEMPLATE HELPERS
# -------------------------------------------------------------------

def _get_template_font(template_data, section, fallback=DEFAULT_FONT):
    """
    Get the font detected from the uploaded sample resume.

    Some PDF fonts such as CMR12/CMR17 are TeX fonts and may not
    exist on Windows. In that case, use Times New Roman as the
    closest safe DOCX fallback.
    """
    font = (
        template_data
        .get(section, {})
        .get("font")
    )

    if not font:
        return fallback

    unsupported_pdf_fonts = {
        "CMR10",
        "CMR12",
        "CMR17",
        "CMCSC10",
        "CMCSC12",
        "CMCSC17",
        "CMBX10",
        "CMBX12",
        "CMBX17",
    }

    if font.upper() in unsupported_pdf_fonts:
        return fallback

    return font


def _get_body_size(template_data):
    return float(
        template_data
        .get("typography", {})
        .get("body_size", 12)
    )


def _get_header_size(template_data):
    return float(
        template_data
        .get("header", {})
        .get(
            "font_size",
            template_data
            .get("typography", {})
            .get("header_size", 24.8),
        )
    )


def _get_heading_size(template_data):
    return float(
        template_data
        .get("section_heading", {})
        .get("font_size", 17.2)
    )


def _set_run_font(
    run,
    font_name=DEFAULT_FONT,
    font_size=12,
    bold=False,
):
    run.font.name = font_name

    # Ensure the font is applied to all Word character sets.
    run._element.rPr.rFonts.set(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii",
        font_name,
    )
    run._element.rPr.rFonts.set(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hAnsi",
        font_name,
    )
    run._element.rPr.rFonts.set(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}cs",
        font_name,
    )

    run.font.size = Pt(font_size)
    run.bold = bold


def _set_paragraph_spacing(
    paragraph,
    before=0,
    after=0,
    line_spacing=1.0,
):
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.line_spacing = line_spacing


def _configure_document(document, template_data):
    """
    Configure page size, margins and base typography.
    """

    section = document.sections[0]

    page_data = template_data.get("page", {})

    width_inches = float(
        page_data.get("width_inches", 8.27)
    )
    height_inches = float(
        page_data.get("height_inches", 11.69)
    )

    section.page_width = Inches(width_inches)
    section.page_height = Inches(height_inches)

    # ---------------------------------------------------------------
    # Naman CV is a compact one-page A4 resume.
    # These margins keep the generated DOCX visually close.
    # ---------------------------------------------------------------

    section.top_margin = Inches(0.55)
    section.bottom_margin = Inches(0.55)
    section.left_margin = Inches(0.65)
    section.right_margin = Inches(0.65)

    body_font = _get_template_font(
        template_data,
        "body",
    )

    body_size = _get_body_size(
        template_data
    )

    styles = document.styles

    normal = styles["Normal"]

    normal.font.name = body_font
    normal.font.size = Pt(body_size)

    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(2)
    normal.paragraph_format.line_spacing = 1.0

    # ---------------------------------------------------------------
    # Make the document use the same base font for East Asian / etc.
    # ---------------------------------------------------------------

    normal._element.rPr.rFonts.set(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii",
        body_font,
    )
    normal._element.rPr.rFonts.set(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hAnsi",
        body_font,
    )


# -------------------------------------------------------------------
# HEADER
# -------------------------------------------------------------------

def _add_header(
    document,
    personal,
    template_data,
):
    header_size = _get_header_size(
        template_data
    )

    header_font = _get_template_font(
        template_data,
        "header",
    )

    body_font = _get_template_font(
        template_data,
        "body",
    )

    body_size = _get_body_size(
        template_data
    )

    section = document.sections[0]

    section.header.is_linked_to_previous = False
    section.footer.is_linked_to_previous = False

    # ---------------------------------------------------------------
    # NAME
    # ---------------------------------------------------------------

    name = personal.get(
        "name",
        "",
    ).strip()

    if name:
        paragraph = document.add_paragraph()

        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        _set_paragraph_spacing(
            paragraph,
            before=0,
            after=1,
            line_spacing=1.0,
        )

        paragraph.paragraph_format.keep_with_next = True

        run = paragraph.add_run(name)

        _set_run_font(
            run,
            font_name=header_font,
            font_size=header_size,
            bold=False,
        )

    # ---------------------------------------------------------------
    # CONTACT INFORMATION
    # ---------------------------------------------------------------

    contact_parts = []

    for field in (
        "email",
        "phone",
        "location",
        "linkedin",
        "github",
        "website",
    ):
        value = personal.get(
            field,
            "",
        ).strip()

        if value:
            contact_parts.append(value)

    if contact_parts:
        paragraph = document.add_paragraph()

        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        _set_paragraph_spacing(
            paragraph,
            before=0,
            after=7,
            line_spacing=1.0,
        )

        run = paragraph.add_run(
            " | ".join(contact_parts)
        )

        _set_run_font(
            run,
            font_name=body_font,
            font_size=min(body_size, 10),
            bold=False,
        )


# -------------------------------------------------------------------
# SECTION HEADING
# -------------------------------------------------------------------

def _add_section_heading(
    document,
    title,
    template_data,
):
    heading_data = template_data.get(
        "section_heading",
        {},
    )

    heading_font = _get_template_font(
        template_data,
        "section_heading",
    )

    heading_size = _get_heading_size(
        template_data
    )

    alignment_name = (
        heading_data
        .get("alignment", "left")
        .lower()
    )

    if alignment_name == "center":
        alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif alignment_name == "right":
        alignment = WD_ALIGN_PARAGRAPH.RIGHT
    else:
        alignment = WD_ALIGN_PARAGRAPH.LEFT

    paragraph = document.add_paragraph()

    paragraph.alignment = alignment

    # Keep section heading with following content.
    paragraph.paragraph_format.keep_with_next = True

    _set_paragraph_spacing(
        paragraph,
        before=7,
        after=2,
        line_spacing=1.0,
    )

    run = paragraph.add_run(
        title.upper()
    )

    _set_run_font(
        run,
        font_name=heading_font,
        font_size=heading_size,
        bold=True,
    )

    return paragraph


# -------------------------------------------------------------------
# BODY
# -------------------------------------------------------------------

def _add_body_paragraph(
    document,
    text,
    template_data,
    bold_prefix=None,
    after=1,
):
    if not text:
        return

    body_font = _get_template_font(
        template_data,
        "body",
    )

    body_size = _get_body_size(
        template_data
    )

    paragraph = document.add_paragraph()

    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT

    _set_paragraph_spacing(
        paragraph,
        before=0,
        after=after,
        line_spacing=1.0,
    )

    if (
        bold_prefix
        and text.startswith(bold_prefix)
    ):
        first = paragraph.add_run(
            bold_prefix
        )

        _set_run_font(
            first,
            font_name=body_font,
            font_size=body_size,
            bold=True,
        )

        remaining = text[
            len(bold_prefix):
        ]

        if remaining:
            second = paragraph.add_run(
                remaining
            )

            _set_run_font(
                second,
                font_name=body_font,
                font_size=body_size,
                bold=False,
            )
    else:
        run = paragraph.add_run(text)

        _set_run_font(
            run,
            font_name=body_font,
            font_size=body_size,
            bold=False,
        )

    return paragraph


# -------------------------------------------------------------------
# BULLETS
# -------------------------------------------------------------------

def _add_bullet(
    document,
    text,
    template_data,
):
    if not text:
        return

    body_font = _get_template_font(
        template_data,
        "body",
    )

    body_size = _get_body_size(
        template_data
    )

    paragraph = document.add_paragraph()

    paragraph.paragraph_format.left_indent = Inches(
        0.18
    )

    paragraph.paragraph_format.first_line_indent = Inches(
        -0.12
    )

    _set_paragraph_spacing(
        paragraph,
        before=0,
        after=1,
        line_spacing=1.0,
    )

    run = paragraph.add_run(
        f"• {text}"
    )

    _set_run_font(
        run,
        font_name=body_font,
        font_size=body_size,
        bold=False,
    )

    return paragraph


# -------------------------------------------------------------------
# SUMMARY
# -------------------------------------------------------------------

def _add_summary(
    document,
    summary,
    template_data,
):
    if not summary:
        return

    _add_section_heading(
        document,
        "Summary",
        template_data,
    )

    _add_body_paragraph(
        document,
        summary,
        template_data,
    )


# -------------------------------------------------------------------
# EXPERIENCE
# -------------------------------------------------------------------

def _add_experience(
    document,
    experience,
    template_data,
):
    if not experience:
        return

    body_font = _get_template_font(
        template_data,
        "body",
    )

    body_size = _get_body_size(
        template_data
    )

    _add_section_heading(
        document,
        "Work Experience",
        template_data,
    )

    for item in experience:
        role = item.get(
            "role",
            "",
        ).strip()

        company = item.get(
            "company",
            "",
        ).strip()

        location = item.get(
            "location",
            "",
        ).strip()

        heading_parts = []

        if role:
            heading_parts.append(role)

        if company:
            heading_parts.append(company)

        heading = " — ".join(
            heading_parts
        )

        if location:
            heading = (
                f"{heading} | {location}"
                if heading
                else location
            )

        if heading:
            paragraph = document.add_paragraph()

            _set_paragraph_spacing(
                paragraph,
                before=2,
                after=0,
                line_spacing=1.0,
            )

            paragraph.paragraph_format.keep_with_next = True

            run = paragraph.add_run(
                heading
            )

            _set_run_font(
                run,
                font_name=body_font,
                font_size=body_size,
                bold=True,
            )

        dates = []

        start_date = item.get(
            "start_date",
            "",
        ).strip()

        end_date = item.get(
            "end_date",
            "",
        ).strip()

        if start_date:
            dates.append(start_date)

        if item.get("current"):
            dates.append("Present")
        elif end_date:
            dates.append(end_date)

        if dates:
            _add_body_paragraph(
                document,
                " - ".join(dates),
                template_data,
                after=1,
            )

        for bullet in item.get(
            "bullets",
            [],
        ):
            _add_bullet(
                document,
                bullet,
                template_data,
            )


# -------------------------------------------------------------------
# PROJECTS
# -------------------------------------------------------------------

def _add_projects(
    document,
    projects,
    template_data,
):
    if not projects:
        return

    body_font = _get_template_font(
        template_data,
        "body",
    )

    body_size = _get_body_size(
        template_data
    )

    _add_section_heading(
        document,
        "Projects",
        template_data,
    )

    for project in projects:
        name = project.get(
            "name",
            "",
        ).strip()

        if name:
            paragraph = document.add_paragraph()

            _set_paragraph_spacing(
                paragraph,
                before=2,
                after=0,
                line_spacing=1.0,
            )

            paragraph.paragraph_format.keep_with_next = True

            run = paragraph.add_run(name)

            _set_run_font(
                run,
                font_name=body_font,
                font_size=body_size,
                bold=True,
            )

        description = project.get(
            "description",
            "",
        ).strip()

        if description:
            _add_body_paragraph(
                document,
                description,
                template_data,
            )

        technologies = project.get(
            "technologies",
            [],
        )

        if technologies:
            paragraph = document.add_paragraph()

            _set_paragraph_spacing(
                paragraph,
                before=0,
                after=1,
                line_spacing=1.0,
            )

            category_run = paragraph.add_run(
                "Technologies: "
            )

            _set_run_font(
                category_run,
                font_name=body_font,
                font_size=body_size,
                bold=True,
            )

            value_run = paragraph.add_run(
                ", ".join(technologies)
            )

            _set_run_font(
                value_run,
                font_name=body_font,
                font_size=body_size,
                bold=False,
            )

        for bullet in project.get(
            "bullets",
            [],
        ):
            _add_bullet(
                document,
                bullet,
                template_data,
            )


# -------------------------------------------------------------------
# EDUCATION
# -------------------------------------------------------------------

def _add_education(
    document,
    education,
    template_data,
):
    if not education:
        return

    body_font = _get_template_font(
        template_data,
        "body",
    )

    body_size = _get_body_size(
        template_data
    )

    _add_section_heading(
        document,
        "Education",
        template_data,
    )

    for item in education:
        degree = item.get(
            "degree",
            "",
        ).strip()

        institution = item.get(
            "institution",
            "",
        ).strip()

        heading_parts = []

        if degree:
            heading_parts.append(degree)

        if institution:
            heading_parts.append(institution)

        heading = " — ".join(
            heading_parts
        )

        if heading:
            paragraph = document.add_paragraph()

            _set_paragraph_spacing(
                paragraph,
                before=1,
                after=0,
                line_spacing=1.0,
            )

            run = paragraph.add_run(
                heading
            )

            _set_run_font(
                run,
                font_name=body_font,
                font_size=body_size,
                bold=True,
            )

        location = item.get(
            "location",
            "",
        ).strip()

        if location:
            _add_body_paragraph(
                document,
                location,
                template_data,
            )

        dates = []

        start_date = item.get(
            "start_date",
            "",
        ).strip()

        end_date = item.get(
            "end_date",
            "",
        ).strip()

        if start_date:
            dates.append(start_date)

        if end_date:
            dates.append(end_date)

        if dates:
            _add_body_paragraph(
                document,
                " - ".join(dates),
                template_data,
            )

        grade = item.get(
            "grade",
            "",
        ).strip()

        if grade:
            _add_body_paragraph(
                document,
                f"Grade: {grade}",
                template_data,
            )


# -------------------------------------------------------------------
# CERTIFICATIONS
# -------------------------------------------------------------------

def _add_certifications(
    document,
    certifications,
    template_data,
):
    if not certifications:
        return

    _add_section_heading(
        document,
        "Certifications",
        template_data,
    )

    for item in certifications:
        name = item.get(
            "name",
            "",
        ).strip()

        issuer = item.get(
            "issuer",
            "",
        ).strip()

        text = name

        if issuer:
            text = (
                f"{name} — {issuer}"
                if name
                else issuer
            )

        if text:
            _add_bullet(
                document,
                text,
                template_data,
            )


# -------------------------------------------------------------------
# PUBLICATIONS
# -------------------------------------------------------------------

def _add_publications(
    document,
    publications,
    template_data,
):
    if not publications:
        return

    _add_section_heading(
        document,
        "Publications",
        template_data,
    )

    for item in publications:
        title = item.get(
            "title",
            "",
        ).strip()

        authors = item.get(
            "authors",
            "",
        ).strip()

        venue = item.get(
            "venue",
            "",
        ).strip()

        parts = []

        if title:
            parts.append(title)

        if authors:
            parts.append(authors)

        if venue:
            parts.append(venue)

        if parts:
            _add_bullet(
                document,
                " — ".join(parts),
                template_data,
            )


# -------------------------------------------------------------------
# SKILLS
# -------------------------------------------------------------------

def _add_skills(
    document,
    skills,
    template_data,
):
    if not skills:
        return

    body_font = _get_template_font(
        template_data,
        "body",
    )

    body_size = _get_body_size(
        template_data
    )

    _add_section_heading(
        document,
        "Skills",
        template_data,
    )

    for category, values in skills.items():
        if not values:
            continue

        paragraph = document.add_paragraph()

        _set_paragraph_spacing(
            paragraph,
            before=0,
            after=1,
            line_spacing=1.0,
        )

        category_run = paragraph.add_run(
            f"{category}: "
        )

        _set_run_font(
            category_run,
            font_name=body_font,
            font_size=body_size,
            bold=True,
        )

        value_run = paragraph.add_run(
            ", ".join(values)
        )

        _set_run_font(
            value_run,
            font_name=body_font,
            font_size=body_size,
            bold=False,
        )


# -------------------------------------------------------------------
# MAIN RENDERER
# -------------------------------------------------------------------

def render_resume_to_docx(
    content,
    template_data=None,
    output_path=None,
):
    """
    Render structured resume content into DOCX.

    The sample resume is used as a visual template through the
    analyzed template_data:
        - A4 page
        - detected typography
        - detected font sizes
        - section heading sizing
        - header sizing
        - one-column structure
        - compact spacing

    The generated content itself remains editable.
    """

    if not content:
        raise ValueError(
            "Resume content is empty."
        )

    template_data = template_data or {}

    document = Document()

    _configure_document(
        document,
        template_data,
    )

    personal = content.get(
        "personal",
        {},
    )

    _add_header(
        document,
        personal,
        template_data,
    )

    _add_summary(
        document,
        content.get("summary", ""),
        template_data,
    )

    _add_experience(
        document,
        content.get("experience", []),
        template_data,
    )

    _add_projects(
        document,
        content.get("projects", []),
        template_data,
    )

    _add_education(
        document,
        content.get("education", []),
        template_data,
    )

    _add_publications(
        document,
        content.get("publications", []),
        template_data,
    )

    _add_certifications(
        document,
        content.get("certifications", []),
        template_data,
    )

    _add_skills(
        document,
        content.get("skills", {}),
        template_data,
    )

    if output_path is None:
        output_dir = (
            Path(settings.MEDIA_ROOT)
            / "generated_resumes"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            output_dir
            / "generated_resume.docx"
        )

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    document.save(
        str(output_path)
    )

    return output_path