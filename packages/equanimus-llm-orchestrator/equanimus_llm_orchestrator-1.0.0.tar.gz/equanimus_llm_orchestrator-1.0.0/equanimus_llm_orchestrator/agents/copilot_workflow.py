from langgraph.graph import StateGraph, START, END

from equanimus_llm_orchestrator.agents.states.copilot_state import CopilotState

from equanimus_llm_orchestrator.agents.nodes.copilot_nodes import (
    add_input_to_context_node,
    generate_response_node,
    map_inputs_note,
    should_summarize_conversation,
    summarize_conversation_node,
    add_message_to_context_node,
)

from equanimus_llm_orchestrator.agents.edges.copilot_edges import count_input_size


def create_copilot_workflow():
    """
    Create and configure the workflow for the conversation.
    """
    copilot_workflow = StateGraph(CopilotState)
    # Add nodes
    copilot_workflow.add_node("summarize_conversation", summarize_conversation_node)
    copilot_workflow.add_node("map_inputs", map_inputs_note)
    copilot_workflow.add_node("add_input_to_context", add_input_to_context_node)
    copilot_workflow.add_node("generate_response", generate_response_node)
    copilot_workflow.add_node("add_message_to_context", add_message_to_context_node)
    # Add edges
    copilot_workflow.add_conditional_edges(START, count_input_size)
    copilot_workflow.add_edge("map_inputs", "add_input_to_context")
    copilot_workflow.add_conditional_edges("add_input_to_context", should_summarize_conversation)
    copilot_workflow.add_conditional_edges("summarize_conversation", should_summarize_conversation)
    copilot_workflow.add_conditional_edges("add_message_to_context", should_summarize_conversation)
    copilot_workflow.add_edge("generate_response", END)

    return copilot_workflow
