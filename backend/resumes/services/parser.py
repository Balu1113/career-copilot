from pathlib import Path

from docx import Document
from pypdf import PdfReader


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

    paragraphs = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n".join(paragraphs)


def extract_resume_text(file):
    extension = Path(file.name).suffix.lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file)

    if extension == ".docx":
        return extract_text_from_docx(file)

    raise ValueError("Unsupported file format.")