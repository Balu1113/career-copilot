from pydantic import BaseModel, Field


class EnrichmentItemOutput(BaseModel):
    item_id: str
    item_type: str
    title: str = ""
    subtitle: str = ""
    current_description: list[str] = Field(default_factory=list)
    weakness_reason: str = ""


class EnrichmentQuestionOutput(BaseModel):
    question_id: str
    item_id: str
    question: str
    placeholder: str = ""


class ResumeEnrichmentAnalysisOutput(BaseModel):
    items_to_enrich: list[EnrichmentItemOutput] = Field(default_factory=list)
    questions: list[EnrichmentQuestionOutput] = Field(default_factory=list)
    analysis_summary: str = ""


class EnhancedBulletsOutput(BaseModel):
    additional_bullets: list[str] = Field(min_length=1, max_length=4)


class RegeneratedBulletsOutput(BaseModel):
    new_bullets: list[str] = Field(min_length=2, max_length=5)
    change_summary: str = ""


class RegeneratedSkillsOutput(BaseModel):
    new_skills: list[str] = Field(min_length=1)
    change_summary: str = ""