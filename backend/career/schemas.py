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