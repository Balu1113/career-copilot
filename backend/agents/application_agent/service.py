from typing import Any

from agents.application_agent.graph import build_application_agent


def run_application_agent(
    *,
    job: dict[str, Any],
    resume: dict[str, Any],
) -> dict[str, Any]:
    """
    Run the application-preparation agent.

    The workflow prepares the application package and stops at
    human approval. It does not submit the application.
    """

    job_description = (
        job.get("description")
        or ""
    ).strip()

    if not job_description:
        raise ValueError(
            "The selected job does not contain a job description."
        )

    initial_state = {
        "job": job,
        "job_description": job_description,
        "resume": resume,
        "resume_context": (
            resume.get("extracted_text")
            or resume.get("content")
            or ""
        ),
        "resume_intelligence": (
            resume.get("resume_intelligence")
            or {}
        ),
        "completed_nodes": [],
        "approval_required": True,
        "approved": False,
        "error": "",
    }

    graph = build_application_agent()

    result = graph.invoke(initial_state)

    if result.get("error"):
        raise ValueError(result["error"])

    return result