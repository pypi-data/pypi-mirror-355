from langgraph.graph import StateGraph, START

from equanimus_llm_orchestrator.agents.states.copilot_state import CopilotState
from equanimus_llm_orchestrator.agents.nodes.clone_chat_nodes import start_clone_node


def create_clone_workflow():
    """
    Create and configure the workflow for the conversation.
    """
    clone_workflow = StateGraph(CopilotState)
    # Add nodes
    clone_workflow.add_node("start_clone", start_clone_node)
    # Add edges
    clone_workflow.add_edge(START, "start_clone")

    return clone_workflow
