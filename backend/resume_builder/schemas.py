from pydantic import BaseModel, Field


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