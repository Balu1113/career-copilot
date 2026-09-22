from langgraph.config import get_stream_writer


def emit_event(event):
    """
    Send a custom LangGraph streaming event.

    If the node is executed outside a streaming context,
    silently ignore the streaming writer.
    """
    try:
        writer = get_stream_writer()
        writer(event)
    except RuntimeError:
        pass


def run_node(node_name, node_function, state):
    completed_nodes = list(state.get("completed_nodes", []))

    emit_event({
        "type": "node_started",
        "node": node_name,
    })

    try:
        result = node_function(state)

        completed_nodes.append(node_name)

        emit_event({
            "type": "node_finished",
            "node": node_name,
        })

        return {
            **result,
            "current_node": node_name,
            "completed_nodes": completed_nodes,
            "error": "",
        }

    except Exception as exc:
        error_message = f"{node_name}: {str(exc)}"

        emit_event({
            "type": "node_failed",
            "node": node_name,
            "message": error_message,
        })

        return {
            "current_node": node_name,
            "completed_nodes": completed_nodes,
            "error": error_message,
        }