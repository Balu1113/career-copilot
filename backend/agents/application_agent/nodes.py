from typing import Any

from agents.services.job_analyzer import analyze_job_description
from career.services.resume_optimizer import optimize_resume_for_job


def prepare_job_requirements(state: dict[str, Any]) -> dict[str, Any]:
    """
    Extract structured requirements from the selected job.
    """

    job_description = state.get("job_description", "").strip()

    if not job_description:
        raise ValueError("Job description is required.")

    job_requirements = analyze_job_description(
        job_description=job_description
    )

    return {
        "job_requirements": job_requirements,
        "current_node": "prepare_job_requirements",
    }


def prepare_resume_context(state: dict[str, Any]) -> dict[str, Any]:
    """
    Prepare the selected resume information for the application workflow.
    """

    resume = state.get("resume") or {}

    resume_context = resume.get("extracted_text", "")

    if not resume_context:
        resume_context = resume.get("content", "")

    if not resume_context:
        raise ValueError("Resume content is required.")

    return {
        "resume_context": resume_context,
        "resume_intelligence": resume.get(
            "resume_intelligence",
            {},
        ),
        "current_node": "prepare_resume_context",
    }


def analyze_candidate_fit(state: dict[str, Any]) -> dict[str, Any]:
    """
    Reuse the existing resume/job analysis information.

    The actual detailed resume analysis will be connected to the
    existing career-analysis services in the next iteration.
    """

    job_requirements = state.get("job_requirements") or {}
    resume_intelligence = state.get("resume_intelligence") or {}

    if not job_requirements:
        raise ValueError("Job requirements are missing.")

    if not resume_intelligence:
        raise ValueError("Resume intelligence is missing.")

    return {
        "resume_analysis": {
            "status": "ready",
            "job_requirements_available": True,
            "resume_intelligence_available": True,
        },
        "current_node": "analyze_candidate_fit",
    }


def optimize_candidate_resume(state: dict[str, Any]) -> dict[str, Any]:
    """
    Generate evidence-based resume optimization suggestions.

    This uses the existing Resume Optimization service and does not
    invent experience or skills.
    """

    resume_context = state.get("resume_context", "").strip()
    job_description = state.get("job_description", "").strip()
    job_requirements = state.get("job_requirements") or {}

    if not resume_context:
        raise ValueError("Resume context is missing.")

    if not job_description:
        raise ValueError("Job description is missing.")

    optimization = optimize_resume_for_job(
        resume_context=resume_context,
        job_description=job_description,
        job_requirements=job_requirements,
    )

    return {
        "optimization": optimization,
        "current_node": "optimize_candidate_resume",
    }


def prepare_application_data(
    state: dict[str, Any],
) -> dict[str, Any]:
    """
    Prepare the information that the user should review before
    submitting an application.
    """

    job = state.get("job") or {}
    resume = state.get("resume") or {}
    optimization = state.get("optimization") or {}

    application_data = {
        "job_title": job.get("title", ""),
        "company": job.get("company", ""),
        "location": job.get("location", ""),
        "job_url": job.get("apply_link") or job.get("job_url", ""),
        "resume_id": resume.get("id"),
        "resume_type": resume.get("type", "uploaded"),
        "safe_ats_keywords": optimization.get(
            "safe_ats_keywords",
            [],
        ),
        "optimization_summary": optimization.get(
            "optimization_summary",
            "",
        ),
        "cover_letter": "",
        "candidate_confirmation_required": True,
    }

    return {
        "application_data": application_data,
        "approval_required": True,
        "approved": False,
        "current_node": "prepare_application_data",
    }


def require_human_approval(
    state: dict[str, Any],
) -> dict[str, Any]:
    """
    Stop the workflow before any external application submission.

    The agent can prepare an application, but the user must explicitly
    approve it before a submission step can ever run.
    """

    return {
        "approval_required": True,
        "approved": False,
        "current_node": "require_human_approval",
    }