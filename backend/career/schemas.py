from pydantic import BaseModel


class RoadmapSkill(BaseModel):
    skill: str
    priority: str
    reason: str


class RoadmapTopic(BaseModel):
    topic: str
    skill: str
    priority: str
    outcome: str


class RoadmapProject(BaseModel):
    name: str
    purpose: str
    skills: list[str]
    description: str


class RoadmapPhase(BaseModel):
    phase: str
    objective: str
    skills: list[str]
    topics: list[str]
    projects: list[str]


class CareerRoadmapOutput(BaseModel):
    title: str
    target_role: str
    summary: str
    skills_to_learn: list[RoadmapSkill]
    learning_topics: list[RoadmapTopic]
    recommended_projects: list[RoadmapProject]
    phases: list[RoadmapPhase]
    immediate_next_steps: list[str]


class RoadmapLessonSection(BaseModel):
    heading: str
    content: str


class RoadmapTutorLesson(BaseModel):
    title: str
    overview: str
    learning_objectives: list[str]
    prerequisites: list[str]
    key_concepts: list[str]
    sections: list[RoadmapLessonSection]
    walkthrough: str
    example: str
    common_mistakes: list[str]
    practice_exercises: list[str]
    project_challenge: str
    assessment_questions: list[str]
    checkpoint: str
    mastery_checklist: list[str]
    next_steps: list[str]
    estimated_time: str


class RoadmapLessonOutline(BaseModel):
    content_type: str
    item_index: int
    level: str
    title: str
    overview: str
    estimated_time: str


class RoadmapLessonPlan(BaseModel):
    lessons: list[RoadmapLessonOutline]