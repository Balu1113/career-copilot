from langgraph.graph import END, START, StateGraph

from agents.application_agent.nodes import (
    analyze_candidate_fit,
    prepare_application_data,
    prepare_job_requirements,
    prepare_resume_context,
    optimize_candidate_resume,
    require_human_approval,
)
from agents.application_agent.state import ApplicationAgentState


def build_application_agent():
    workflow = StateGraph(ApplicationAgentState)

    workflow.add_node(
        "prepare_job_requirements",
        prepare_job_requirements,
    )

    workflow.add_node(
        "prepare_resume_context",
        prepare_resume_context,
    )

    workflow.add_node(
        "analyze_candidate_fit",
        analyze_candidate_fit,
    )

    workflow.add_node(
        "optimize_candidate_resume",
        optimize_candidate_resume,
    )

    workflow.add_node(
        "prepare_application_data",
        prepare_application_data,
    )

    workflow.add_node(
        "require_human_approval",
        require_human_approval,
    )

    workflow.add_edge(
        START,
        "prepare_job_requirements",
    )

    workflow.add_edge(
        "prepare_job_requirements",
        "prepare_resume_context",
    )

    workflow.add_edge(
        "prepare_resume_context",
        "analyze_candidate_fit",
    )

    workflow.add_edge(
        "analyze_candidate_fit",
        "optimize_candidate_resume",
    )

    workflow.add_edge(
        "optimize_candidate_resume",
        "prepare_application_data",
    )

    workflow.add_edge(
        "prepare_application_data",
        "require_human_approval",
    )

    workflow.add_edge(
        "require_human_approval",
        END,
    )

    return workflow.compile()