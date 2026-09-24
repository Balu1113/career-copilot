from typing import TypedDict


class CareerState(TypedDict, total=False):
    job_description: str

    resume_context: str

    resume_intelligence: dict

    job_requirements: dict

    resume_analysis: dict

    skill_gap_analysis: dict

    career_recommendation: dict

    interview_preparation: dict

    current_node: str

    completed_nodes: list[str]

    error: str