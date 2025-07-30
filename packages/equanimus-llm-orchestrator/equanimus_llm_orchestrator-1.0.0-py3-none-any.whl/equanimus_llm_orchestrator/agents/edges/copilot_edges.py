from django.conf import settings
from equanimus_llm_orchestrator.agents.states.copilot_state import CopilotState


def count_input_size(state: CopilotState):
    llm = state.get("llm")
    messages = state.get("messages")
    last_message = messages[-1].type
    last_message_type = messages[-1].content

    if last_message_type != "human":
        return "add_message_to_context"

    num_tokens = llm.get_num_tokens(last_message)

    if num_tokens > settings.LLM_MAX_INPUT_TOKENS:
        return "map_inputs"
    else:
        return "add_message_to_context"
