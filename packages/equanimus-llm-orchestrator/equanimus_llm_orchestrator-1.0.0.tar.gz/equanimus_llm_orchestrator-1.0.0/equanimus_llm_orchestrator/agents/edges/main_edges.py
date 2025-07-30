from equanimus_llm_orchestrator.agents.states.main_state import MainState


def router(state: MainState):
    chat_mode = state.get("chat_mode")

    if chat_mode == "copilot":
        return "copilot"
    elif chat_mode == "rag":
        return "rag"
    elif chat_mode == "clone":
        return "clone"
    else:
        return "copilot"
