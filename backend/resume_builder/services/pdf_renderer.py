from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


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


def _section_heading(title, styles):
    return [
        Spacer(1, 5),
        Paragraph(title.upper(), styles["section"]),
        HRFlowable(width="100%", thickness=0.55, color=colors.HexColor("#888888"), spaceBefore=1, spaceAfter=4),
    ]


def _add_contact_links(personal, styles):
    fields = ("email", "phone", "location", "linkedin", "github", "website")
    values = [str(personal.get(field, "") or "").strip() for field in fields]
    values = [value for value in values if value]

    if not values:
        return []

    return [Paragraph(" | ".join(values), styles["Contact"]), Spacer(1, 4)]


def render_resume_to_pdf(content, output_path, template_data=None):
    if (template_data or {}).get("uploaded_layout"):
        return render_uploaded_resume_to_pdf(
            content,
            output_path,
        )

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
    styles.add(ParagraphStyle(
        name="ResumeName",
        parent=styles["Normal"],
        fontName=BODY_FONT,
        fontSize=24,
        leading=26,
        alignment=TA_CENTER,
        textColor=TEXT_COLOR,
        spaceAfter=1,
    ))
    styles.add(ParagraphStyle(
        name="Contact",
        parent=styles["Normal"],
        fontName=BODY_FONT,
        fontSize=8.5,
        leading=10,
        alignment=TA_CENTER,
        textColor=LINK_COLOR,
    ))
    styles.add(ParagraphStyle(
        name="section",
        parent=styles["Normal"],
        fontName=BODY_FONT,
        fontSize=15,
        leading=17,
        textColor=TEXT_COLOR,
        spaceBefore=0,
        spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        name="body",
        parent=styles["Normal"],
        fontName=BODY_FONT,
        fontSize=9.5,
        leading=11.2,
        textColor=TEXT_COLOR,
        alignment=TA_LEFT,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="small",
        parent=styles["Normal"],
        fontName=BODY_FONT,
        fontSize=9,
        leading=10.5,
        textColor=TEXT_COLOR,
    ))
    styles.add(ParagraphStyle(
        name="bold_small",
        parent=styles["small"],
        fontName=BOLD_FONT,
    ))
    styles.add(ParagraphStyle(
        name="right_small",
        parent=styles["small"],
        alignment=TA_RIGHT,
    ))

    personal = content.get("personal") or {}
    story = [
        _paragraph(personal.get("name") or "Your Name", styles["ResumeName"]),
        *_add_contact_links(personal, styles),
    ]

    summary = str(content.get("summary", "") or "").strip()
    if summary:
        story.extend(_section_heading("Summary", styles))
        story.append(_paragraph(summary, styles["body"]))

    experience = content.get("experience") or []
    if experience:
        story.extend(_section_heading("Work Experience", styles))
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

    projects = content.get("projects") or []
    if projects:
        story.extend(_section_heading("Projects", styles))
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

    education = content.get("education") or []
    if education:
        story.extend(_section_heading("Education", styles))
        rows = []
        for item in education:
            degree = item.get("degree") or "Degree"
            institution = item.get("institution") or "Institution"
            dates = _join_date_range(item)
            grade = item.get("grade") or ""
            rows.append([
                _paragraph(dates, styles["small"]),
                _paragraph(f"<b>{degree}</b> at <b>{institution}</b>", styles["small"]),
                _paragraph(grade, styles["right_small"]),
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

    publications = content.get("publications") or []
    if publications:
        story.extend(_section_heading("Publications", styles))
        for item in publications:
            parts = [item.get("authors"), item.get("title"), item.get("venue"), item.get("date"), item.get("url")]
            story.append(_paragraph(". ".join(str(part).strip() for part in parts if str(part or "").strip()), styles["body"]))

    skills = content.get("skills") or {}
    if skills:
        story.extend(_section_heading("Skills", styles))
        rows = []
        for category, values in skills.items():
            rows.append([_paragraph(category, styles["small"]), _paragraph(", ".join(values or []), styles["small"])])
        table = Table(rows, colWidths=[1.15 * inch, 5.3 * inch])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        story.append(table)

    document.build(story)


def render_uploaded_resume_to_pdf(content, output_path):
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
    styles.add(ParagraphStyle(name="UploadName", parent=styles["Normal"], fontName=BODY_FONT, fontSize=18, leading=20, alignment=TA_CENTER, textColor=TEXT_COLOR))
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

    education = content.get("education") or []
    if education:
        story.extend(heading("Education"))
        for item in education:
            dates = _join_date_range(item)
            degree = item.get("degree") or "Degree"
            institution = item.get("institution") or "Institution"
            grade = item.get("grade") or ""
            story.append(row_table([[
                Paragraph(f"<b>{degree}</b> at <b>{institution}</b>", styles["UploadBody"]),
                Paragraph(dates, styles["UploadRight"]),
                Paragraph(grade, styles["UploadRight"]),
            ]], [4.55 * inch, 1.0 * inch, 0.9 * inch]))

    projects = content.get("projects") or []
    if projects:
        story.extend(heading("Projects"))
        for item in projects:
            story.append(Paragraph(f"<b>{item.get('name') or 'Project'}</b>", styles["UploadBody"]))
            if item.get("description"):
                story.append(Paragraph(str(item["description"]), styles["UploadBody"]))
            technologies = item.get("technologies") or []
            if technologies:
                story.append(Paragraph(f"Technologies: {', '.join(technologies)}", styles["UploadBody"]))
            for bullet in item.get("bullets") or []:
                if str(bullet or "").strip():
                    story.append(Paragraph(f"- {bullet}", styles["UploadBody"]))

    skills = content.get("skills") or {}
    if skills:
        story.extend(heading("Technical Skills and Tools"))
        rows = [[Paragraph(f"<b>{category}</b>", styles["UploadBody"]), Paragraph(", ".join(values or []), styles["UploadBody"])] for category, values in skills.items()]
        story.append(row_table(rows, [1.25 * inch, 5.2 * inch]))

    certifications = content.get("certifications") or []
    if certifications:
        story.extend(heading("Certifications"))
        for item in certifications:
            issuer = f" - {item.get('issuer')}" if item.get("issuer") else ""
            story.append(Paragraph(f"- {item.get('name') or 'Certification'}{issuer}", styles["UploadBody"]))

    publications = content.get("publications") or []
    if publications:
        story.extend(heading("Publications"))
        for item in publications:
            parts = [item.get("authors"), item.get("title"), item.get("venue"), item.get("date"), item.get("url")]
            story.append(Paragraph("- " + ". ".join(str(part).strip() for part in parts if str(part or "").strip()), styles["UploadBody"]))

    document.build(story)
