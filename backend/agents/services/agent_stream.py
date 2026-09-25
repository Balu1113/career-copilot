import json

from agents.graph import build_career_graph


def stream_career_analysis(resume_context, job_description, resume_intelligence,):
    graph = build_career_graph()

    initial_state = {
        "job_description": job_description,
        "resume_context": resume_context,
        "resume_intelligence": resume_intelligence,
        "completed_nodes": [],
        "error": "",
    }

    try:
        for chunk in graph.stream(
            initial_state,
            stream_mode=["updates", "custom"],
            version="v2",
        ):
            # -----------------------------------------
            # Custom events
            # -----------------------------------------
            if chunk["type"] == "custom":
                event = chunk["data"]

                if event["type"] == "node_started":
                    yield {
                        "type": "node_started",
                        "node": event["node"],
                    }

                elif event["type"] == "node_finished":
                    # Completion is emitted from the
                    # actual LangGraph state update below.
                    pass

                elif event["type"] == "node_failed":
                    yield {
                        "type": "workflow_error",
                        "node": event["node"],
                        "message": event["message"],
                    }

                    return

            # -----------------------------------------
            # Actual LangGraph node output
            # -----------------------------------------
            elif chunk["type"] == "updates":
                for node_name, node_output in chunk["data"].items():

                    yield {
                        "type": "node_completed",
                        "node": node_name,
                        "data": node_output,
                    }

                    if node_output.get("error"):
                        yield {
                            "type": "workflow_error",
                            "node": node_name,
                            "message": node_output["error"],
                        }

                        return

    except Exception as exc:
        yield {
            "type": "workflow_error",
            "node": "",
            "message": str(exc),
        }