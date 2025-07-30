from equanimus_llm_orchestrator.agents.states.rag_state import RagState
from equanimus_llm_orchestrator.document_loaders.utils.utils import count_token_in_documents
from django.conf import settings


def check_has_file(state: RagState):
    """
    Check if the file exists.
    """
    file_path = state.get("file_path")
    if file_path:
        return "load_file"
    else:
        return "find_documents_vector_db"

def check_documents_tokens(state: RagState):
    """
    Check if number of tokens in document.
    """
    documents = state.get("documents")
    llm = state.get("llm")
    num_tokens = count_token_in_documents(documents, llm)

    if num_tokens > settings.LLM_MAX_CONTEXT_TOKENS:
        return "summarize_documents"
    else:
        return "load_documents_to_context"

def check_has_documents(state: RagState):
    """
    Check if the documents exists.
    """
    documents = state.get("documents", [])
    if documents and len(documents) > 0:
        return "check_documents"
    else:
        return "copilot_agent"

def check_has_context(state: RagState):
    """
    Check if the context exists.
    """
    context = state.get("context")
    if context:
        return "copilot_agent"
    else:
        return "not_loaded_file"