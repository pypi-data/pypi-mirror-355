from langgraph.constants import Send
from typing import Literal

from equanimus_llm_orchestrator.agents.states.summarizations_state import OverallSummaryState
from equanimus_llm_orchestrator.document_loaders.utils.utils import count_token_in_documents
from django.conf import settings


def map_summaries(state: OverallSummaryState):
    llm = state.get("llm")
    contents = state.get("contents")
    return [
        Send("generate_summary", {"content": content, "llm": llm}) for content in contents
    ]

def should_collapse(
    state: OverallSummaryState,
) -> Literal["collapse_summaries", "generate_final_summary"]:
    llm = state.get("llm")

    collapsed_summaries = state.get("collapsed_summaries")

    num_tokens = count_token_in_documents(collapsed_summaries, llm)

    if num_tokens > settings.LLM_MAX_INPUT_TOKENS:
        return "collapse_summaries"
    else:
        return "generate_final_summary"
