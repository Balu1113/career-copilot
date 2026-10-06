from typing import Literal

from pydantic import BaseModel, Field


ResumeSection = Literal[
    "summary",
    "experience",
    "projects",
    "education",
    "publications",
    "certifications",
    "skills",
]

DEFAULT_RESUME_SECTION_ORDER = [
    "summary",
    "experience",
    "projects",
    "education",
    "publications",
    "certifications",
    "skills",
]


def ordered_resume_sections(content, template_data=None):
    """Return a complete, duplicate-free order for supported resume sections."""
    requested_order = content.get("section_order")
    if not isinstance(requested_order, list):
        template_sections = (template_data or {}).get("sections", [])
        if isinstance(template_sections, list):
            section_aliases = {
                "professional summary": "summary",
                "career summary": "summary",
                "work experience": "experience",
                "professional experience": "experience",
                "technical skills": "skills",
                "certificates": "certifications",
                "certificate": "certifications",
                "project": "projects",
                "publication": "publications",
            }
            requested_order = [
                section_aliases.get(
                    str(section).strip().lower(),
                    str(section).strip().lower(),
                )
                for section in template_sections
            ]
        else:
            requested_order = DEFAULT_RESUME_SECTION_ORDER

    result = []
    for section in requested_order + DEFAULT_RESUME_SECTION_ORDER:
        if section in DEFAULT_RESUME_SECTION_ORDER and section not in result:
            result.append(section)
    return result


class ResumePersonalInfo(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""


class ResumeExperience(BaseModel):
    company: str = ""
    role: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    current: bool = False
    bullets: list[str] = Field(default_factory=list)


class ResumeProject(BaseModel):
    name: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    url: str = ""
    bullets: list[str] = Field(default_factory=list)


class ResumeEducation(BaseModel):
    degree: str = ""
    institution: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    grade: str = ""


class ResumeCertification(BaseModel):
    name: str = ""
    issuer: str = ""
    date: str = ""
    url: str = ""


class ResumePublication(BaseModel):
    title: str = ""
    authors: str = ""
    venue: str = ""
    date: str = ""
    url: str = ""


class ResumeOptimization(BaseModel):
    """
    Only AI-controlled portions of an existing resume.
    """

    skills: dict[str, list[str]] = Field(
        default_factory=dict
    )

    projects: list[ResumeProject] = Field(
        default_factory=list
    )


class ResumeSummaryOutput(BaseModel):
    summary: str = ""


class GeneratedResumeContent(BaseModel):
    """
    Complete editable resume structure.
    """

    personal: ResumePersonalInfo = Field(
        default_factory=ResumePersonalInfo
    )

    summary: str = ""

    skills: dict[str, list[str]] = Field(
        default_factory=dict
    )

    experience: list[ResumeExperience] = Field(
        default_factory=list
    )

    projects: list[ResumeProject] = Field(
        default_factory=list
    )

    education: list[ResumeEducation] = Field(
        default_factory=list
    )

    certifications: list[ResumeCertification] = Field(
        default_factory=list
    )

    publications: list[ResumePublication] = Field(
        default_factory=list
    )

    section_order: list[ResumeSection] = Field(
        default_factory=lambda: DEFAULT_RESUME_SECTION_ORDER.copy()
    )