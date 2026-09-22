from langgraph.graph import END, START, StateGraph

from .state import CareerState
from .nodes.resume_intelligence import resume_intelligence_node
from .nodes.job_analyzer import job_analyzer_node
from .nodes.resume_analyzer import resume_analyzer_node
from .nodes.skill_gap import skill_gap_node
from .nodes.career_advisor import career_advisor_node
from .node_runner import run_node
from .nodes.interview_prep import interview_prep_node

def wrapped_resume_intelligence(state):
    return run_node(
        "resume_intelligence",
        resume_intelligence_node,
        state,
    )


def wrapped_job_analyzer(state):
    return run_node(
        "job_analyzer",
        job_analyzer_node,
        state,
    )


def wrapped_resume_analyzer(state):
    return run_node(
        "resume_analyzer",
        resume_analyzer_node,
        state,
    )


def wrapped_skill_gap(state):
    return run_node(
        "skill_gap",
        skill_gap_node,
        state,
    )


def wrapped_career_advisor(state):
    return run_node(
        "career_advisor",
        career_advisor_node,
        state,
    )

def wrapped_interview_prep(state):
    return run_node(
        "interview_prep",
        interview_prep_node,
        state,
    )


def should_continue(state):
    if state.get("error"):
        return "stop"

    return "continue"


def build_career_graph():

    graph = StateGraph(CareerState)

    graph.add_node(
        "resume_intelligence",
        wrapped_resume_intelligence,
    )

    graph.add_node(
        "job_analyzer",
        wrapped_job_analyzer,
    )

    graph.add_node(
        "resume_analyzer",
        wrapped_resume_analyzer,
    )

    graph.add_node(
        "skill_gap",
        wrapped_skill_gap,
    )

    graph.add_node(
        "career_advisor",
        wrapped_career_advisor,
    )

    graph.add_node(
        "interview_prep",
        wrapped_interview_prep,
    )

    graph.add_edge(
        START,
        "resume_intelligence",
    )

    graph.add_conditional_edges(
        "resume_intelligence",
        should_continue,
        {
            "continue": "job_analyzer",
            "stop": END,
        },
    )

    graph.add_conditional_edges(
        "job_analyzer",
        should_continue,
        {
            "continue": "resume_analyzer",
            "stop": END,
        },
    )

    graph.add_conditional_edges(
        "resume_analyzer",
        should_continue,
        {
            "continue": "skill_gap",
            "stop": END,
        },
    )

    graph.add_conditional_edges(
        "skill_gap",
        should_continue,
        {
            "continue": "career_advisor",
            "stop": END,
        },
    )

    graph.add_conditional_edges(
        "career_advisor",
        should_continue,
        {
            "continue": "interview_prep",
            "stop": END,
        },
    )

    graph.add_edge(
        "interview_prep",
        END,
    )

    return graph.compile()