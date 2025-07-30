from langgraph.graph import END, StateGraph, START

from equanimus_llm_orchestrator.agents.states.main_state import MainState
from equanimus_llm_orchestrator.agents.nodes.main_nodes import (
    copilot_agent_node,
    get_response_node,
    rag_agent_node,
    clone_agent_node,
)

from equanimus_llm_orchestrator.agents.edges.main_edges import router


def create_main_workflow():
    """
    Create and configure the workflow for the conversation.
    """
    main_workflow = StateGraph(MainState)
    # Add nodes
    main_workflow.add_node("copilot", copilot_agent_node)
    main_workflow.add_node("rag", rag_agent_node)
    main_workflow.add_node("clone", clone_agent_node)
    main_workflow.add_node("generate_response", get_response_node)

    # Add edges
    main_workflow.add_conditional_edges(
        START,
        router,
    )
    main_workflow.add_edge("copilot", "generate_response")
    main_workflow.add_edge("clone", "generate_response")
    main_workflow.add_edge("rag", END)
    main_workflow.add_edge("generate_response", END)

    return main_workflow
