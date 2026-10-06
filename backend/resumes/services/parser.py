from pathlib import Path

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from pypdf import PdfReader
from docx.table import Table
from docx.text.paragraph import Paragraph


def extract_text_from_pdf(file):
    reader = PdfReader(file)

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)


def extract_text_from_docx(file):
    document = Document(file)

    blocks = []

    for block in document.element.body.iterchildren():
        if isinstance(block, CT_P):
            text = Paragraph(block, document).text.strip()
            if text:
                blocks.append(text)
        elif isinstance(block, CT_Tbl):
            table = Table(block, document)
            for row in table.rows:
                cells = [
                    " ".join(
                        paragraph.text.strip()
                        for paragraph in cell.paragraphs
                        if paragraph.text.strip()
                    )
                    for cell in row.cells
                ]
                row_text = " | ".join(value for value in cells if value)
                if row_text:
                    blocks.append(row_text)

    for section in document.sections:
        for part in (section.header, section.footer):
            blocks.extend(
                paragraph.text.strip()
                for paragraph in part.paragraphs
                if paragraph.text.strip()
            )

    return "\n".join(blocks)


def extract_resume_text(file):
    extension = Path(file.name).suffix.lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file)

    if extension == ".docx":
        return extract_text_from_docx(file)

    raise ValueError("Unsupported file format.")