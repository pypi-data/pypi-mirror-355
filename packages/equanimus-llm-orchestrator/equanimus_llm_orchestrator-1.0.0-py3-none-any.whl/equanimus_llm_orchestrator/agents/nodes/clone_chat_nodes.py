from equanimus_llm_orchestrator.agents.states.copilot_state import CopilotState


def start_clone_node(state: CopilotState):
    """
    Start the conversation clone.
    """
    messages = state.get("messages", [])
    llm = state.get("llm")
    response = llm.invoke(messages)

    return {"messages": messages, "response": response.content}
