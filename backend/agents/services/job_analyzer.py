"""Plain-function access to the job analyzer.

``agents.nodes.job_analyzer`` exposes the analyzer as a LangGraph node that
takes (and returns) a state dict. The application agent needs the same
analysis as a standalone call, so this module adapts one to the other.
"""

from agents.nodes.job_analyzer import job_analyzer_node


def analyze_job_description(*, job_description: str) -> dict:
    """Return structured job requirements for a job description."""
    result = job_analyzer_node({"job_description": job_description})
    return result.get("job_requirements") or {}
