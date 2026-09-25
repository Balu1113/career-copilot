from typing import Any, TypedDict


class ApplicationAgentState(TypedDict, total=False):
    # Job information
    job: dict[str, Any]
    job_description: str
    job_requirements: dict[str, Any]

    # Resume information
    resume: dict[str, Any]
    resume_context: str
    resume_intelligence: dict[str, Any]

    # Existing career analysis
    resume_analysis: dict[str, Any]
    skill_gap_analysis: dict[str, Any]

    # Resume optimization
    optimization: dict[str, Any]

    # Generated application information
    application_data: dict[str, Any]

    # Human approval
    approval_required: bool
    approved: bool

    # Workflow tracking
    current_node: str
    completed_nodes: list[str]
    error: str