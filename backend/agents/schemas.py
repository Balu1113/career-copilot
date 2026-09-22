from pydantic import BaseModel


class JobRequirements(BaseModel):
    required_skills: list[str]
    preferred_skills: list[str]
    responsibilities: list[str]
    experience_requirements: list[str]
    education_requirements: list[str]


class MatchingExperience(BaseModel):
    company: str
    role: str
    description: list[str]
    technologies: list[str]


class ResumeAnalysis(BaseModel):
    matching_skills: list[str]
    matching_experience: list[MatchingExperience]
    demonstrated_tools: list[str]
    relevant_projects: list[str]


class SkillGapItem(BaseModel):
    skill: str
    priority: str
    reason: str


class PriorityGap(BaseModel):
    skill: str
    priority: str
    reason: str


class SkillGapAnalysis(BaseModel):
    missing_skills: list[SkillGapItem]
    partial_skills: list[SkillGapItem]
    priority_gaps: list[PriorityGap]
    explanation: str

class RecommendedTopic(BaseModel):
    topic: str
    priority: str
    reason: str
    source_gaps: list[str]


class RecommendedProject(BaseModel):
    name: str
    description: str
    technologies: list[str]


class CareerInterviewPreparation(BaseModel):

    topic: str

    guidance: str


class InterviewQuestion(BaseModel):

    question: str

    category: str

    difficulty: str

    reason: str


class InterviewPreparationPlan(BaseModel):

    technical_questions: list[InterviewQuestion]

    project_questions: list[InterviewQuestion]

    gap_based_questions: list[InterviewQuestion]

    behavioral_questions: list[InterviewQuestion]

    preparation_topics: list[str]

class NextStep(BaseModel):
    step: str
    priority: str


class CareerRecommendation(BaseModel):

    match_summary: str

    recommended_topics: list[RecommendedTopic]

    recommended_projects: list[RecommendedProject]

    interview_preparation: list[CareerInterviewPreparation]

    next_steps: list[NextStep]

class Project(BaseModel):
    name: str
    description: list[str]
    technologies: list[str]

class Education(BaseModel):
    institution: str
    degree: str
    dates: str


class Certification(BaseModel):
    name: str
    issuer: str

class Experience(BaseModel):
    company: str
    role: str
    description: list[str]
    technologies: list[str]

class ResumeIntelligence(BaseModel):
    professional_summary: str
    skills: list[str]
    programming_languages: list[str]
    frameworks: list[str]
    tools_and_technologies: list[str]
    ai_ml_technologies: list[str]
    projects: list[Project]
    experience: list[Experience]
    education: list[Education]
    certifications: list[Certification]