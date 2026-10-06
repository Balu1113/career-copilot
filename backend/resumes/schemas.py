"""Pydantic schemas for resume tailoring: LLM output + API response shapes."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, Field


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


StringList = Annotated[list[str], BeforeValidator(_string_list)]
OptionalString = Annotated[str | None, BeforeValidator(_optional_string)]


class ResumePersonalInfo(BaseModel):
    name: str = ""
    title: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    website: str = ""
    linkedin: str = ""
    github: str = ""


class ResumeWorkExperience(BaseModel):
    id: int | None = None
    title: str = ""
    company: str = ""
    location: str = ""
    years: str = ""
    description: StringList = Field(default_factory=list)
    descriptionStyles: StringList = Field(default_factory=list)


class ResumeEducation(BaseModel):
    id: int | None = None
    institution: str = ""
    degree: str = ""
    years: str = ""
    description: str = ""


class ResumePersonalProject(BaseModel):
    id: int | None = None
    name: str = ""
    role: str = ""
    years: str = ""
    description: StringList = Field(default_factory=list)
    descriptionStyles: StringList = Field(default_factory=list)


class ResumeCustomItem(BaseModel):
    id: int | None = None
    title: str = ""
    subtitle: str = ""
    years: str = ""
    description: StringList = Field(default_factory=list)
    descriptionStyles: StringList = Field(default_factory=list)


class ResumeCustomSection(BaseModel):
    sectionType: Literal["itemList", "text"] = "itemList"
    items: list[ResumeCustomItem] = Field(default_factory=list)
    text: str = ""


class ResumeAdditional(BaseModel):
    technicalSkills: StringList = Field(default_factory=list)
    certificationsTraining: StringList = Field(default_factory=list)
    languages: StringList = Field(default_factory=list)
    awards: StringList = Field(default_factory=list)


class ResumeData(BaseModel):
    """Structured resume payload shared by preview/confirm/PDF flows."""

    personalInfo: ResumePersonalInfo = Field(default_factory=ResumePersonalInfo)
    summary: str = ""
    workExperience: list[ResumeWorkExperience] = Field(default_factory=list)
    education: list[ResumeEducation] = Field(default_factory=list)
    personalProjects: list[ResumePersonalProject] = Field(default_factory=list)
    additional: ResumeAdditional = Field(default_factory=ResumeAdditional)
    customSections: dict[str, ResumeCustomSection] = Field(default_factory=dict)


class JobKeywords(BaseModel):
    company: str = ""
    role: str = ""
    required_skills: StringList = Field(default_factory=list)
    preferred_skills: StringList = Field(default_factory=list)
    experience_requirements: StringList = Field(default_factory=list)
    education_requirements: StringList = Field(default_factory=list)
    key_responsibilities: StringList = Field(default_factory=list)
    keywords: StringList = Field(default_factory=list)
    experience_years: int | None = None
    seniority_level: str = ""


class SkillTarget(BaseModel):
    skill: str = ""
    reason: str = ""


class SkillTargetPlanOutput(BaseModel):
    target_skills: list[SkillTarget] = Field(default_factory=list)
    strategy_notes: str = ""


class ResumeChange(BaseModel):
    path: str
    action: Literal["replace", "append", "reorder", "add_skill"] = "replace"
    original: OptionalString = None
    value: Any = None
    reason: str = ""


class ResumeDiffOutput(BaseModel):
    changes: list[ResumeChange] = Field(default_factory=list)
    strategy_notes: str = ""


class InterviewQuestion(BaseModel):
    question: str = ""
    focus_area: str = ""
    suggested_answer_points: StringList = Field(default_factory=list)


class InterviewSkillGap(BaseModel):
    skill: str = ""
    why_it_matters: str = ""
    preparation_suggestion: str = ""


class InterviewPrepData(BaseModel):
    role_fit_analysis: StringList = Field(default_factory=list)
    resume_questions: list[InterviewQuestion] = Field(default_factory=list)
    project_follow_ups: list[InterviewQuestion] = Field(default_factory=list)
    skill_gaps: list[InterviewSkillGap] = Field(default_factory=list)
    talking_points: StringList = Field(default_factory=list)


class RefinementStats(BaseModel):
    passes_completed: int = 0
    keywords_injected: int = 0
    final_match_percentage: float = 0.0
    ai_phrases_removed: int = 0


class ATSSubScores(BaseModel):
    keyword_match: float = 0.0
    skills_coverage: float = 0.0
    experience_alignment: float = 0.0
    content_quality: float = 0.0


class ATSScore(BaseModel):
    overall_score: float = 0.0
    sub_scores: ATSSubScores = Field(default_factory=ATSSubScores)
    missing_keywords: StringList = Field(default_factory=list)
    injectable_keywords: StringList = Field(default_factory=list)
    recommendations: StringList = Field(default_factory=list)


class ResumeFieldDiff(BaseModel):
    path: str
    section: str
    change_type: Literal["modified", "added", "removed"]
    original: str = ""
    improved: str = ""


class ResumeDiffSummary(BaseModel):
    total_changes: int = 0
    modified: int = 0
    added: int = 0
    removed: int = 0
    sections_changed: StringList = Field(default_factory=list)


class Improvement(BaseModel):
    suggestion: str
    lineNumber: int | None = None


class RawResume(BaseModel):
    id: int | None = None
    content: str = ""
    content_type: str = "md"
    created_at: str = ""
    processing_status: str = "pending"


class ResumeFetchData(BaseModel):
    resume_id: int
    raw_resume: RawResume
    processed_resume: ResumeData | None = None
    cover_letter: str | None = None
    outreach_message: str | None = None
    interview_prep: InterviewPrepData | None = None
    parent_id: int | None = None
    title: str | None = None


class ResumeFetchResponse(BaseModel):
    request_id: str
    data: ResumeFetchData


class ResumeSummary(BaseModel):
    resume_id: int
    filename: str | None = None
    is_master: bool = False
    parent_id: int | None = None
    processing_status: str = "pending"
    created_at: str = ""
    updated_at: str = ""
    title: str | None = None


class ResumeListResponse(BaseModel):
    request_id: str
    data: list[ResumeSummary]


class ResumeUploadResponse(BaseModel):
    message: str
    request_id: str
    resume_id: int
    processing_status: str
    is_master: bool = False


class ImproveResumeData(BaseModel):
    request_id: str
    resume_id: int | None = None
    preview_id: int | None = None
    preview_expires_at: str | None = None
    job_id: int
    resume_preview: ResumeData | None = None
    improvements: list[Improvement] = Field(default_factory=list)
    markdownOriginal: str = ""
    markdownImproved: str = ""
    cover_letter: str | None = None
    outreach_message: str | None = None
    interview_prep: InterviewPrepData | None = None
    diff_summary: ResumeDiffSummary | None = None
    detailed_changes: list[ResumeFieldDiff] | None = None
    refinement_stats: RefinementStats | None = None
    ats_score: ATSScore | None = None
    warnings: list[str] = Field(default_factory=list)
    refinement_attempted: bool = False
    refinement_successful: bool = False


class ImproveResumeResponse(BaseModel):
    request_id: str
    data: ImproveResumeData


class GenerateContentResponse(BaseModel):
    content: str
    message: str


class GenerateInterviewPrepResponse(BaseModel):
    interview_prep: InterviewPrepData
    message: str
