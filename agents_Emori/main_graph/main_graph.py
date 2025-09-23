from langgraph.graph import StateGraph
from shared.state import MainState
from subgraph_a.subgraph_a import create_subgraph_a
from subgraph_b.subgraph_b import create_subgraph_b
from .main_node import (  # Changed from main_nodes
    load_memory_node,
    merge_path_AandB_node,
    answer_generator_node,
    evaluator_node,
    save_memory_node
)

def create_main_graph():
    workflow = StateGraph(MainState)
    
    # Add individual nodes
    workflow.add_node("load_memory", load_memory_node)
    workflow.add_node("subgraph_a", create_subgraph_a())
    workflow.add_node("subgraph_b", create_subgraph_b())
    workflow.add_node("merge_paths", merge_path_AandB_node)
    workflow.add_node("answer_generator", answer_generator_node)
    workflow.add_node("evaluator", evaluator_node)
    workflow.add_node("save_memory", save_memory_node)
    
    # Add edges
    workflow.set_entry_point("load_memory")
    workflow.add_edge("load_memory", "subgraph_a")
    workflow.add_edge("load_memory", "subgraph_b")
    workflow.add_edge(["subgraph_a", "subgraph_b"], "merge_paths")
    workflow.add_edge("merge_paths", "answer_generator")
    workflow.add_edge("answer_generator", "evaluator")
    
    # Conditional edge for evaluator loop
    workflow.add_conditional_edges(
        "evaluator",
        lambda state: state["evaluation_result"],
        {
            "ok": "save_memory",
            "Not ok": "answer_generator"
        }
    )
    
    workflow.set_finish_point("save_memory")
    
    return workflow.compile()