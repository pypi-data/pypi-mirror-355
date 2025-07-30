from langgraph.graph import END, START, StateGraph

from equanimus_llm_orchestrator.agents.states.summarizations_state import OverallSummaryState

from equanimus_llm_orchestrator.agents.nodes.summary_doc_nodes import (
    generate_summary_node,
    collect_summaries_node,
    collapse_summaries_node,
    generate_final_summary_node,
)

from equanimus_llm_orchestrator.agents.edges.summary_doc_edges import (
    map_summaries,
    should_collapse,
)


def create_summarization_workflow():
    """
    Create and configure the workflow for the summary.
    """
    summarization_workflow = StateGraph(OverallSummaryState)
    summarization_workflow.add_node("generate_summary", generate_summary_node)
    summarization_workflow.add_node("collect_summaries", collect_summaries_node)
    summarization_workflow.add_node("collapse_summaries", collapse_summaries_node)
    summarization_workflow.add_node("generate_final_summary", generate_final_summary_node)

    # Edges:
    summarization_workflow.add_conditional_edges(START, map_summaries, ["generate_summary"])
    summarization_workflow.add_edge("generate_summary", "collect_summaries")
    summarization_workflow.add_conditional_edges("collect_summaries", should_collapse)
    summarization_workflow.add_conditional_edges("collapse_summaries", should_collapse)
    summarization_workflow.add_edge("generate_final_summary", END)

    return summarization_workflow
