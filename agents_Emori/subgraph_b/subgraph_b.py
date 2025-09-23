from langgraph.graph import StateGraph
from shared.state import MainState
from .subgraph_b_nodes import (
    semantic_search_b_node,  # Fixed: actual function name
    intensity_score,
    top_k_filter,
    merge_path_B,
    calculator_func,
    warning_gen_flag
)

# Build the actual subgraph B structure
def create_subgraph_b():
    workflow = StateGraph(MainState)
    
    # Add nodes
    workflow.add_node("semantic_search_b", semantic_search_b_node)
    workflow.add_node("intensity_score", intensity_score)
    workflow.add_node("top_k_filter", top_k_filter)
    workflow.add_node("merge_path_B", merge_path_B)
    workflow.add_node("calculator_func", calculator_func)
    workflow.add_node("warning_gen_flag", warning_gen_flag)
    
    # Add edges - parallel execution after semantic_search_b
    workflow.set_entry_point("semantic_search_b")
    workflow.add_edge("semantic_search_b", "intensity_score")
    workflow.add_edge("semantic_search_b", "top_k_filter")
    workflow.add_edge(["intensity_score", "top_k_filter"], "merge_path_B")
    workflow.add_edge("merge_path_B", "calculator_func")
    workflow.add_edge("calculator_func", "warning_gen_flag")
    workflow.set_finish_point("warning_gen_flag")
    
    return workflow.compile()