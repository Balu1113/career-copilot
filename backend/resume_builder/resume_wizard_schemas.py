from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


WizardSection = Literal[
    "intro",
    "contact",
    "summary",
    "workExperience",
    "internships",
    "education",
    "personalProjects",
    "skills",
    "review",
]


class ResumeWizardResumeData(BaseModel):
    model_config = ConfigDict(extra="allow")

    personalInfo: dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    workExperience: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    personalProjects: list[dict[str, Any]] = Field(default_factory=list)
    additional: dict[str, Any] = Field(default_factory=dict)
    sectionMeta: list[dict[str, Any]] = Field(default_factory=list)
    customSections: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_entry_ids(self):
        for section in (self.workExperience, self.education, self.personalProjects):
            seen = set()
            for entry in section:
                entry_id = entry.get("id", 0)
                if isinstance(entry_id, bool) or not isinstance(entry_id, int) or entry_id < 0:
                    raise ValueError("Resume entry IDs must be non-negative integers.")
                if entry_id > 0 and entry_id in seen:
                    raise ValueError("Positive resume entry IDs must be unique per section.")
                if entry_id > 0:
                    seen.add(entry_id)
        return self


class ResumeWizardNextQuestion(BaseModel):
    text: str
    section: WizardSection


class ResumeWizardTurnOutput(BaseModel):
    resume_data: ResumeWizardResumeData
    next_question: ResumeWizardNextQuestion
    inferred_skills: list[str] = Field(default_factory=list)
    is_complete: bool = False