def resume_intelligence_node(state):
    resume_intelligence = state.get(
        "resume_intelligence",
        {}
    )

    if not resume_intelligence:
        raise ValueError(
            "Resume intelligence is missing from the workflow state."
        )

    return {
        "resume_intelligence": resume_intelligence,
    }