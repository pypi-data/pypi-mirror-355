from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from django.conf import settings

from langchain.chains.combine_documents.reduce import (
    collapse_docs,
    split_list_of_docs,
)



from equanimus_llm_orchestrator.agents.states.summarizations_state import (
    SummaryState,
    OverallSummaryState
)

from equanimus_llm_orchestrator.chat_prompts.templates_prompts import reduce_prompt, map_prompt
from equanimus_llm_orchestrator.document_loaders.utils.utils import count_token_in_documents


def _reduce(input: dict, llm: BaseChatModel) -> str:
    prompt = reduce_prompt().invoke(input)
    response = llm.invoke(prompt)
    return response.content

def generate_summary_node(state: SummaryState):
    llm = state.get("llm")
    content = state.get("content")
    prompt = map_prompt().invoke(content)
    response = llm.invoke(prompt)
    return {"summaries": [response.content]}


def collect_summaries_node(state: OverallSummaryState):
    summaries = state.get("summaries", [])
    return {
        "collapsed_summaries": [Document(summary) for summary in summaries]
    }

def collapse_summaries_node(state: OverallSummaryState):
    llm = state.get("llm")
    doc_lists = split_list_of_docs(
        state["collapsed_summaries"],
        count_token_in_documents,
        settings.LLM_MAX_INPUT_TOKENS,
        llm

    )
    results = []
    for doc_list in doc_lists:
        results.append(collapse_docs(doc_list, _reduce))

    return {"collapsed_summaries": results}


def generate_final_summary_node(state: OverallSummaryState):
    collapsed_summaries = state.get("collapsed_summaries", [])
    llm = state.get("llm")

    response =  _reduce(collapsed_summaries, llm)

    return {"final_summary": response}

