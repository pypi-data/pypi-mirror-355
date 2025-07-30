from langgraph.graph import StateGraph, START, END

from equanimus_llm_orchestrator.agents.states.rag_state import RagState
from equanimus_llm_orchestrator.agents.nodes.rag_nodes import (
    load_file_node,
    find_documents_vector_db_node,
    summarize_documents_node,
    load_documents_to_context_node,
    check_documents_node,
    load_summary_to_context_node,
    not_loaded_file_node,
)

from equanimus_llm_orchestrator.agents.edges.rag_edges import (
    check_has_file,
    check_documents_tokens,
    check_has_documents,
    check_has_context,
)


def create_rag_workflow():
    from equanimus_llm_orchestrator.agents.nodes.main_nodes import copilot_agent_node

    """
    Create and configure the workflow for the conversation.
    """
    rag_workflow = StateGraph(RagState)
    # Add nodes
    rag_workflow.add_node("load_file", load_file_node)
    rag_workflow.add_node("find_documents_vector_db", find_documents_vector_db_node)
    rag_workflow.add_node("summarize_documents", summarize_documents_node)
    rag_workflow.add_node("load_summary_to_context", load_summary_to_context_node)
    rag_workflow.add_node("load_documents_to_context", load_documents_to_context_node)
    rag_workflow.add_node("copilot_agent", copilot_agent_node)
    rag_workflow.add_node("check_documents", check_documents_node)
    rag_workflow.add_node("not_loaded_file", not_loaded_file_node)

    # Add edges
    rag_workflow.add_conditional_edges(START, check_has_file)
    rag_workflow.add_conditional_edges("check_documents", check_documents_tokens)
    rag_workflow.add_edge("load_file", "check_documents")
    rag_workflow.add_conditional_edges("load_documents_to_context", check_has_context)
    rag_workflow.add_edge("summarize_documents", "load_summary_to_context")
    rag_workflow.add_edge("load_summary_to_context", "copilot_agent")
    rag_workflow.add_conditional_edges("find_documents_vector_db", check_has_documents)
    rag_workflow.add_edge("not_loaded_file", END)
    rag_workflow.add_edge("copilot_agent", END)
    return rag_workflow
