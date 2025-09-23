from typing import TypedDict, Optional, List, Dict, Any, Union, Annotated
from operator import add

class MainState(TypedDict):
    user_query: Annotated[str, lambda x, y: x or y]
    user_id: Annotated[str, lambda x, y: x or y]
    answer: Optional[str]
    past_conversation: Annotated[Optional[List[Dict[str, str]]], lambda x, y: x or y]
    
    # PATH A
    semantic_search_a_results: Annotated[Optional[List[Dict[str, str]]], add]
    graded_documents: Optional[List[Dict[str, Union[str, int]]]] 
    label: Optional[str]

    # PATH B
    semantic_search_b_results: Annotated[Optional[List[Dict[str, Union[str, float]]]], add]
    intensity_score: Optional[Dict[str, Any]]
    top_k_results: Optional[List[Dict[str, Union[str, float]]]]
    
    # Calculator fields - all need annotations since load_memory returns them
    user_scores: Annotated[Optional[Dict[str, float]], lambda x, y: x or y]
    user_decay_scores: Annotated[Optional[Dict[str, float]], lambda x, y: x or y]
    last_update_timestamp: Annotated[Optional[str], lambda x, y: x or y]
    calc_result: Annotated[Optional[float], lambda x, y: x or y]
    
    warning_text: Optional[str] 
    evaluation_result: Optional[str]
    evaluation_feedback: Optional[str]