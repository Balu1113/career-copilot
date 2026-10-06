from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    KeepInFrame,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from resume_builder.schemas import ordered_resume_sections


BODY_FONT = "Times-Roman"
BOLD_FONT = "Times-Bold"
LINK_COLOR = colors.HexColor("#174ea6")
TEXT_COLOR = colors.HexColor("#222222")


def _paragraph(text, style):
    value = str(text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(value.replace("\n", "<br/>"), style)


def _join_date_range(item):
    start = str(item.get("start_date", "") or "").strip()
    end = str(item.get("end_date", "") or "").strip()

    if item.get("current") and not end:
        end = "Present"

    return " - ".join(part for part in (start, end) if part)


def _section_heading(title, styles, template_data=None, page_width=None):
    template_data = template_data or {}
    preview = template_data.get("preview", {})
    heading_style = preview.get("heading_style", "")
    alignment = (
        TA_CENTER
        if template_data.get("section_heading", {}).get("alignment") == "center"
        else TA_RIGHT
        if template_data.get("section_heading", {}).get("alignment") == "right"
        else TA_LEFT
    )
    heading = Paragraph(title.upper(), styles["section"])
    heading.style.alignment = alignment

    if heading_style == "underline":
        heading.style.underline = True
        heading.style.underlineColor = styles.accent
    elif heading_style == "caps":
        heading.style.letterSpacing = 1

    if heading_style == "bar" and page_width:
        heading_table = Table([[heading]], colWidths=[page_width])
        heading_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LINEBEFORE", (0, 0), (0, 0), 2.5, styles.accent),
        ]))
        return [
            Spacer(1, 5),
            heading_table,
            HRFlowable(width="100%", thickness=0.55, color=styles["accent"], spaceBefore=1, spaceAfter=4),
        ]

    rule_color = (
        styles.accent
        if heading_style in {"rule", "underline"}
        else colors.HexColor("#888888")
    )
    return [
        Spacer(1, 5),
        heading,
        HRFlowable(width="100%", thickness=0.55, color=rule_color, spaceBefore=1, spaceAfter=4),
    ]


def _add_contact_links(personal, styles):
    fields = ("email", "phone", "location", "linkedin", "github", "website")
    values = [str(personal.get(field, "") or "").strip() for field in fields]
    values = [value for value in values if value]

    if not values:
        return []

    return [Paragraph(" | ".join(values), styles["Contact"]), Spacer(1, 4)]


def _fit_story_to_page(story, document):
    flattened_story = []
    for flowable in story:
        if isinstance(flowable, KeepTogether):
            flattened_story.extend(flowable._content)
        else:
            flattened_story.append(flowable)

    return KeepInFrame(
        document.width,
        document.height,
        flattened_story,
        mode="shrink",
        hAlign="LEFT",
        vAlign="TOP",
    )


def render_resume_to_pdf(content, output_path, template_data=None):
    template_data = template_data or {}
    if template_data.get("uploaded_layout") and not template_data.get("preview"):
        return render_uploaded_resume_to_pdf(
            content,
            output_path,
            fit_to_page=(template_data or {}).get("fit_to_page", False),
        )

    page_data = template_data.get("page", {})
    margin_right = float(page_data.get("margin_right", 0.55))
    margin_left = float(page_data.get("margin_left", 0.55))
    margin_top = float(page_data.get("margin_top", 0.48))
    margin_bottom = float(page_data.get("margin_bottom", 0.48))
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=margin_right * inch,
        leftMargin=margin_left * inch,
        topMargin=margin_top * inch,
        bottomMargin=margin_bottom * inch,
        title=str((content.get("personal") or {}).get("name", "Resume")),
    )

    preview_data = template_data.get("preview", {})
    accent_hex = str(preview_data.get("accent", "222222")).lstrip("#")
    try:
        accent = colors.HexColor(f"#{accent_hex}")
    except (ValueError, TypeError):
        accent = TEXT_COLOR
    accent_soft_hex = str(
        preview_data.get("accent_soft", "F3F4F6")
    ).lstrip("#")
    try:
        accent_soft = colors.HexColor(f"#{accent_soft_hex}")
    except (ValueError, TypeError):
        accent_soft = colors.HexColor("#F3F4F6")
    header_style = preview_data.get("header_style", "centered")
    header_alignment = template_data.get("header", {}).get(
        "alignment",
        preview_data.get("header_align", "center"),
    )
    header_alignment = (
        TA_LEFT
        if header_alignment == "left"
        else TA_RIGHT
        if header_alignment == "right"
        else TA_CENTER
    )
    typography = template_data.get("typography", {})
    template_font = str(
        typography.get("font")
        or template_data.get("body", {}).get("font")
        or ""
    ).lower()
    if any(font in template_font for font in ("arial", "calibri", "segoe", "helvetica")):
        body_font, bold_font = "Helvetica", "Helvetica-Bold"
    elif "courier" in template_font:
        body_font, bold_font = "Courier", "Courier-Bold"
    else:
        body_font, bold_font = BODY_FONT, BOLD_FONT
    header_size = float(
        template_data.get("header", {}).get("font_size", 24)
    )
    heading_size = float(
        template_data.get("section_heading", {}).get("font_size", 15)
    )
    body_size = float(typography.get("body_size", 9.5))
    header_size = min(header_size, 24)
    heading_size = min(heading_size, 15)
    body_size = min(body_size, 9.5)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ResumeName",
        parent=styles["Normal"],
        fontName=body_font,
        fontSize=header_size,
        leading=header_size + 2,
        alignment=header_alignment,
        textColor=colors.white if header_style == "band" else accent,
        spaceAfter=1,
    ))
    styles.add(ParagraphStyle(
        name="Contact",
        parent=styles["Normal"],
        fontName=body_font,
        fontSize=8.5,
        leading=10,
        alignment=header_alignment,
        textColor=colors.white if header_style == "band" else LINK_COLOR,
    ))
    styles.add(ParagraphStyle(
        name="section",
        parent=styles["Normal"],
        fontName=body_font,
        fontSize=heading_size,
        leading=heading_size + 2,
        textColor=accent,
        spaceBefore=0,
        spaceAfter=0,
    ))
    styles.accent = accent
    styles.add(ParagraphStyle(
        name="body",
        parent=styles["Normal"],
        fontName=body_font,
        fontSize=body_size,
        leading=body_size * 1.18,
        textColor=TEXT_COLOR,
        alignment=TA_LEFT,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="small",
        parent=styles["Normal"],
        fontName=body_font,
        fontSize=9,
        leading=10.5,
        textColor=TEXT_COLOR,
    ))
    styles.add(ParagraphStyle(
        name="bold_small",
        parent=styles["small"],
        fontName=bold_font,
    ))
    styles.add(ParagraphStyle(
        name="right_small",
        parent=styles["small"],
        alignment=TA_RIGHT,
    ))

    personal = content.get("personal") or {}
    name_paragraph = _paragraph(
        personal.get("name") or "Your Name",
        styles["ResumeName"],
    )
    contact_paragraphs = _add_contact_links(personal, styles)
    if header_style == "band":
        band_rows = [[name_paragraph]]
        band_rows.extend([[paragraph] for paragraph in contact_paragraphs if isinstance(paragraph, Paragraph)])
        header_table = Table(band_rows, colWidths=[document.width])
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), accent),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story = [header_table, Spacer(1, 4)]
    elif header_style in {"boxed", "accent"}:
        header_table = Table([[name_paragraph]], colWidths=[document.width])
        border_edge = "BOX" if header_style == "boxed" else "LINEBEFORE"
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), accent_soft if header_style == "boxed" else colors.white),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            (border_edge, (0, 0), (-1, -1), 1.5, accent),
        ]))
        story = [header_table, *contact_paragraphs]
    else:
        story = [name_paragraph, *contact_paragraphs]

    for section in ordered_resume_sections(content, template_data):
        if section == "summary":
            summary = str(content.get("summary", "") or "").strip()
            if summary:
                story.extend(_section_heading("Summary", styles, template_data, document.width))
                story.append(_paragraph(summary, styles["body"]))
        elif section == "experience":
            experience = content.get("experience") or []
            if experience:
                story.extend(_section_heading("Work Experience", styles, template_data, document.width))
                for item in experience:
                    heading = Table(
                        [[
                            _paragraph(item.get("role") or "Designation", styles["bold_small"]),
                            _paragraph(_join_date_range(item), styles["right_small"]),
                        ]],
                        colWidths=[4.9 * inch, 1.55 * inch],
                    )
                    heading.setStyle(TableStyle([
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ]))
                    item_flow = [heading]
                    company = str(item.get("company", "") or "").strip()
                    location = str(item.get("location", "") or "").strip()
                    if company or location:
                        item_flow.append(_paragraph(" | ".join(part for part in (company, location) if part), styles["small"]))
                    for bullet in item.get("bullets") or []:
                        if str(bullet or "").strip():
                            item_flow.append(_paragraph(f"- {bullet}", styles["body"]))
                    story.append(KeepTogether(item_flow))
        elif section == "projects":
            projects = content.get("projects") or []
            if projects:
                story.extend(_section_heading("Projects", styles, template_data, document.width))
                for item in projects:
                    name = item.get("name") or "Project"
                    url = item.get("url") or ""
                    header = Table(
                        [[
                            _paragraph(name, styles["bold_small"]),
                            _paragraph(url, styles["right_small"]) if url else "",
                        ]],
                        colWidths=[4.9 * inch, 1.55 * inch],
                    )
                    header.setStyle(TableStyle([
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ]))
                    story.append(header)
                    if item.get("description"):
                        story.append(_paragraph(item["description"], styles["body"]))
                    for bullet in item.get("bullets") or []:
                        if str(bullet or "").strip():
                            story.append(_paragraph(f"- {bullet}", styles["body"]))
        elif section == "education":
            education = content.get("education") or []
            if education:
                story.extend(_section_heading("Education", styles, template_data, document.width))
                rows = []
                for item in education:
                    degree = item.get("degree") or "Degree"
                    institution = item.get("institution") or "Institution"
                    rows.append([
                        _paragraph(_join_date_range(item), styles["small"]),
                        Paragraph(
                            f"<b>{escape(str(degree))}</b> at "
                            f"<b>{escape(str(institution))}</b>",
                            styles["small"],
                        ),
                        _paragraph(item.get("grade") or "", styles["right_small"]),
                    ])
                table = Table(rows, colWidths=[0.9 * inch, 4.55 * inch, 1.0 * inch])
                table.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]))
                story.append(table)
        elif section == "publications":
            publications = content.get("publications") or []
            if publications:
                story.extend(_section_heading("Publications", styles, template_data, document.width))
                for item in publications:
                    parts = [item.get("authors"), item.get("title"), item.get("venue"), item.get("date"), item.get("url")]
                    story.append(_paragraph(". ".join(str(part).strip() for part in parts if str(part or "").strip()), styles["body"]))
        elif section == "certifications":
            certifications = content.get("certifications") or []
            if certifications:
                story.extend(_section_heading("Certifications", styles, template_data, document.width))
                for item in certifications:
                    parts = [item.get("name"), item.get("issuer"), item.get("date")]
                    story.append(_paragraph(" - ".join(str(part).strip() for part in parts if str(part or "").strip()), styles["body"]))
        elif section == "skills":
            skills = content.get("skills") or {}
            if skills:
                story.extend(_section_heading("Skills", styles, template_data, document.width))
                rows = []
                for category, values in skills.items():
                    values = values if isinstance(values, list) else [values]
                    if preview_data.get("skill_style") in {"chips", "grid"}:
                        values_text = "  ".join(
                            f'<font backColor="{accent_soft.hexval()}">'
                            f"  {escape(str(value))}  </font>"
                            for value in values or []
                        )
                    else:
                        values_text = ", ".join(
                            escape(str(value)) for value in values or []
                        )
                    rows.append([
                        _paragraph(category, styles["small"]),
                        Paragraph(values_text, styles["small"]),
                    ])
                table = Table(rows, colWidths=[1.15 * inch, 5.3 * inch])
                table.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3 if preview_data.get("skill_style") == "chips" else 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 2 if preview_data.get("skill_style") == "chips" else 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2 if preview_data.get("skill_style") == "chips" else 1),
                    *(
                        [
                            ("BACKGROUND", (0, 0), (0, -1), accent_soft),
                            ("TEXTCOLOR", (0, 0), (0, -1), accent),
                        ]
                        if preview_data.get("skill_style") in {"chips", "grid"}
                        else []
                    ),
                ]))
                story.append(table)

    if (template_data or {}).get("fit_to_page"):
        story = [_fit_story_to_page(story, document)]
    document.build(story)


def render_uploaded_resume_to_pdf(content, output_path, fit_to_page=False):
    """Render uploaded-resume edits in the source resume's section order."""
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.48 * inch,
        bottomMargin=0.48 * inch,
        title=str((content.get("personal") or {}).get("name", "Resume")),
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="UploadName", parent=styles["Normal"],     fontName=body_font, fontSize=18, leading=20, alignment=TA_CENTER, textColor=TEXT_COLOR))
    styles.add(ParagraphStyle(name="UploadContact", parent=styles["Normal"], fontName=BODY_FONT, fontSize=8, leading=9, alignment=TA_CENTER, textColor=LINK_COLOR))
    styles.add(ParagraphStyle(name="UploadSection", parent=styles["Normal"], fontName=BOLD_FONT, fontSize=10, leading=12, textColor=TEXT_COLOR, spaceBefore=2, spaceAfter=0))
    styles.add(ParagraphStyle(name="UploadBody", parent=styles["Normal"], fontName=BODY_FONT, fontSize=8.2, leading=9.5, textColor=TEXT_COLOR, spaceAfter=1))
    styles.add(ParagraphStyle(name="UploadBold", parent=styles["UploadBody"], fontName=BOLD_FONT))
    styles.add(ParagraphStyle(name="UploadRight", parent=styles["UploadBody"], alignment=TA_RIGHT))

    def heading(title):
        return [
            Spacer(1, 4),
            Paragraph(title.upper(), styles["UploadSection"]),
            HRFlowable(width="100%", thickness=0.6, color=colors.black, spaceBefore=1, spaceAfter=3),
        ]

    def row_table(rows, widths):
        table = Table(rows, colWidths=widths)
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        return table

    personal = content.get("personal") or {}
    contact = [personal.get(field) for field in ("email", "phone", "linkedin", "github", "website")]
    contact = [str(value).strip() for value in contact if str(value or "").strip()]
    story = [
        Paragraph(str(personal.get("name") or "Your Name"), styles["UploadName"]),
        Paragraph(" | ".join(contact), styles["UploadContact"]),
    ]

    section_stories = {}

    summary = str(content.get("summary") or "").strip()
    summary_story = []
    if summary:
        summary_story.extend(heading("Professional Summary"))
        summary_story.append(_paragraph(summary, styles["UploadBody"]))
    section_stories["summary"] = summary_story

    experience = content.get("experience") or []
    experience_story = []
    if experience:
        experience_story.extend(heading("Experience"))
        for item in experience:
            role = item.get("role") or "Role"
            company = item.get("company") or ""
            location = item.get("location") or ""
            employer = " | ".join(value for value in (company, location) if value)
            experience_story.append(
                Paragraph(f"<b>{escape(str(role))}</b>", styles["UploadBody"])
            )
            if employer:
                experience_story.append(_paragraph(employer, styles["UploadBody"]))
            dates = _join_date_range(item)
            if dates:
                experience_story.append(_paragraph(dates, styles["UploadRight"]))
            for bullet in item.get("bullets") or []:
                if str(bullet or "").strip():
                    experience_story.append(
                        _paragraph(f"- {bullet}", styles["UploadBody"])
                    )
    section_stories["experience"] = experience_story

    education = content.get("education") or []
    education_story = []
    if education:
        education_story.extend(heading("Education"))
        for item in education:
            dates = _join_date_range(item)
            degree = item.get("degree") or "Degree"
            institution = item.get("institution") or "Institution"
            grade = item.get("grade") or ""
            education_story.append(row_table([[
                Paragraph(f"<b>{degree}</b> at <b>{institution}</b>", styles["UploadBody"]),
                Paragraph(dates, styles["UploadRight"]),
                Paragraph(grade, styles["UploadRight"]),
            ]], [4.55 * inch, 1.0 * inch, 0.9 * inch]))
    section_stories["education"] = education_story

    projects = content.get("projects") or []
    projects_story = []
    if projects:
        projects_story.extend(heading("Projects"))
        for item in projects:
            projects_story.append(Paragraph(f"<b>{item.get('name') or 'Project'}</b>", styles["UploadBody"]))
            if item.get("description"):
                projects_story.append(Paragraph(str(item["description"]), styles["UploadBody"]))
            technologies = item.get("technologies") or []
            if technologies:
                projects_story.append(Paragraph(f"Technologies: {', '.join(technologies)}", styles["UploadBody"]))
            for bullet in item.get("bullets") or []:
                if str(bullet or "").strip():
                    projects_story.append(Paragraph(f"- {bullet}", styles["UploadBody"]))
    section_stories["projects"] = projects_story

    skills = content.get("skills") or {}
    skills_story = []
    if skills:
        skills_story.extend(heading("Technical Skills and Tools"))
        rows = [[Paragraph(f"<b>{category}</b>", styles["UploadBody"]), Paragraph(", ".join(values or []), styles["UploadBody"])] for category, values in skills.items()]
        skills_story.append(row_table(rows, [1.25 * inch, 5.2 * inch]))
    section_stories["skills"] = skills_story

    certifications = content.get("certifications") or []
    certifications_story = []
    if certifications:
        certifications_story.extend(heading("Certifications"))
        for item in certifications:
            issuer = f" - {item.get('issuer')}" if item.get("issuer") else ""
            certifications_story.append(Paragraph(f"- {item.get('name') or 'Certification'}{issuer}", styles["UploadBody"]))
    section_stories["certifications"] = certifications_story

    publications = content.get("publications") or []
    publications_story = []
    if publications:
        publications_story.extend(heading("Publications"))
        for item in publications:
            parts = [item.get("authors"), item.get("title"), item.get("venue"), item.get("date"), item.get("url")]
            publications_story.append(Paragraph("- " + ". ".join(str(part).strip() for part in parts if str(part or "").strip()), styles["UploadBody"]))
    section_stories["publications"] = publications_story

    for section in ordered_resume_sections(content):
        story.extend(section_stories.get(section, []))

    if fit_to_page:
        story = [_fit_story_to_page(story, document)]
    document.build(story)
