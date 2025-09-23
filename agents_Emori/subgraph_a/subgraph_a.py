from langgraph.graph import StateGraph
from shared.state import MainState
from .subgraph_a_nodes import (  # Changed from path_a_nodes
    filter_generator_node,
    semantic_search_a_node,
    grading_document_node,
    filter_document_node
)

# Build the actual subgraph structure
def create_subgraph_a():
    workflow = StateGraph(MainState)
    
    # Add nodes
    workflow.add_node("filter_generator", filter_generator_node)
    workflow.add_node("semantic_search_a", semantic_search_a_node)
    workflow.add_node("grading_document", grading_document_node)
    workflow.add_node("filter_document", filter_document_node)
    
    # Add edges (linear flow)
    workflow.set_entry_point("filter_generator")
    workflow.add_edge("filter_generator", "semantic_search_a")
    workflow.add_edge("semantic_search_a", "grading_document")
    workflow.add_edge("grading_document", "filter_document")
    workflow.set_finish_point("filter_document")
    
    return workflow.compile()