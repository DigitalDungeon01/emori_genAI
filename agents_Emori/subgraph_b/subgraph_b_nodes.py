import sys
import os
from dotenv import load_dotenv
load_dotenv()

sys.path.append('/app')
from database.milvus_cloud_db.zilliz_retriever_b import semantic_search_b, initialize_retriever_b
from shared.state import MainState
from shared.schemas import SentimentScore, FilteredResult
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from bson import ObjectId
from llm_model.llm import llm_model
from services.calculator_node import MentalHealthCalculator

zilliz_uri_b = os.getenv("ZILLIZ_URI_B")
zilliz_token_b = os.getenv("ZILLIZ_TOKEN_B")

initialize_retriever_b(
    zilliz_uri=zilliz_uri_b,
    zilliz_token=zilliz_token_b,
    collection_name="sentiment_collection_emori", # dont change this
    embedding_model="all-MiniLM-L6-v2",
    use_cuda=False
)


# Initialize calculator
calculator = MentalHealthCalculator()

def semantic_search_b_node(state: MainState) -> MainState:
    try:
        query = state["user_query"]
        search_results = semantic_search_b(query, top_k=30)  
        
        result = [{
            'id': item['id'],
            'similarity': item['similarity_score'],
            'text': item['text'],
            'status': item['status']
        } for item in search_results]
        
        if result:
            print("retrieved document from semantic search b node:")
            #for item in result:
                #print(f"text: {item['text']}")
                #print(f"similarity score: {item['similarity']}")
                #print(f"status: {item['status']}")
        
        return {"semantic_search_b_results": result}
    except Exception as e:
        print(f"Semantic search B failed: {e}")
        return {"semantic_search_b_results": []}


def intensity_score(state: MainState) -> MainState:
    try:
        user_query = state["user_query"]
        prompt = (
            f"Analyze sentiment and context of: {user_query}\n\n"
            "Provide sentiment scores (pos, neg, neu) that sum to 1.0\n"
            "Context types: personal (user's feelings), general (about others), question (asking info), academic (educational)\n"
            "Personal relevance: 0.0=impersonal, 1.0=deeply personal"
        )

        llm_response = llm_model.with_structured_output(SentimentScore).invoke(prompt)

        sentiment_scores = {
            'pos': llm_response.pos,
            'neg': llm_response.neg, 
            'neu': llm_response.neu,
            'context_type': llm_response.context_type,
            'personal_relevance': llm_response.personal_relevance
        }
        
        print(f"pos: {llm_response.pos}, neg: {llm_response.neg}, neu: {llm_response.neu}")
        print(f"context: {llm_response.context_type}, relevance: {llm_response.personal_relevance}")
        
        return {"intensity_score": sentiment_scores}
    except:
        print("fail")
        return {"intensity_score": {}}
    
class FilteredResult(BaseModel):
    id: str = Field(description="Document ID")
    similarity: float = Field(description="Similarity score", ge=0.0, le=1.0)
    status: str = Field(description="Status/label of the document")
    text: str = Field(description="Text content", max_length=350)

class FilterResponse(BaseModel):
    filtered_results: List[FilteredResult] = Field(description="List of filtered relevant results")

def top_k_filter(state: MainState) -> MainState:
    try:
        search_results = state.get("semantic_search_b_results", [])
        
        if not search_results:
            print("no search results to filter")
            return {"top_k_results": []}
        
        user_query = state["user_query"]
        prompt = (
            f"You are an expert mental health assistant. Carefully review the following search results in relation to the user's query:\n"
            f"USER QUERY: {user_query}\n\n"
            "Your task:\n"
            "- Select only the results that are highly relevant to the user's current mental or emotional state based on the user query and the search results and the STATUS.\n"
            "- Exclude any results that are off-topic, generic, or not directly related to the user's mental health.\n"
            "- Pay special attention to any results that indicate a high risk of suicidal ideation, self-harm, severe depression, or anxiety that could lead to self-harm or suicide. If any such results are present, ensure they are included in the filtered list, even if they are few.\n"
            "\nReturn ONLY the filtered results using the provided schema. Do not add any extra commentary or explanation.\n\n"
            "SEARCH RESULTS:\n"
        )
        
        # Limit to first 5 results to avoid token limits
        for i, result in enumerate(search_results[:5], 1):
            prompt += (
                f"{i}. ID: {result['id']}\n"
                f"   Similarity: {result['similarity']:.3f}\n"
                f"   Status: {result['status']}\n"
                f"   Text: {result['text'][:350]}...\n\n"
                
            )
        
        # Create structured LLM with schema
        structured_llm = llm_model.with_structured_output(FilterResponse)
        
        # Get structured response
        llm_response = structured_llm.invoke(prompt)
        
        # Extract the filtered results from the structured response
        filtered_results = []
        for filtered_result in llm_response.filtered_results:
            filtered_results.append({
                "id": filtered_result.id,
                "similarity": filtered_result.similarity,
                "status": filtered_result.status,
                "text": filtered_result.text
            })
        
        print(f"TOP_k node filtered {len(filtered_results)} from {len(search_results)} results")
        print(filtered_results)
        return {"top_k_results": filtered_results}
        
    except Exception as e:
        print(f"filter fail: {e}")
        # Fallback to top 3 results if LLM filtering fails
        fallback_results = search_results[:3]
        return {"top_k_results": fallback_results}
    
    
    

def merge_path_B(state: MainState) -> MainState:
    intensity_score = state.get("intensity_score", {})
    top_k_results = state.get("top_k_results", [])
    
    # Check what data we have
    if intensity_score and top_k_results:
        print("merged!")
    elif not intensity_score and not top_k_results:
        print("intensity-score: null")
        print("top_k: null")
    elif not intensity_score:
        print("intensity-score: null")
    elif not top_k_results:
        print("top_k: null")
    
    # Simple passthrough - no new fields needed
    return {}


# def calculator_func(state: MainState) -> MainState:
#     try:
#         top_k_results = state.get("top_k_results", [])
        
#         # Fix field names to match calculator expectations
#         fixed_top_k = []
#         for result in top_k_results:
#             fixed_result = {
#                 "similarity_score": result["similarity"],  # Fix field name
#                 "label": result["status"],                 # Fix field name  
#                 "text": result["text"],
#                 "id": result["id"]
#             }
#             fixed_top_k.append(fixed_result)
        
#         intensity_score = state.get("intensity_score", {
#             "pos": 0.33, "neg": 0.33, "neu": 0.34,
#             "context_type": "personal", "personal_relevance": 1.0
#         })
        
#         current_scores = state.get("user_scores")
#         decay_scores = state.get("user_decay_scores") 
#         last_update = state.get("last_update_timestamp")
        
#         # Calculate updated scores
#         updated_scores, updated_decay, timestamp, calc_result = calculator.calculate_scores(
#             user_id="temp",  # Not used in calculation logic
#             top_k_results=fixed_top_k,
#             intensity_score=intensity_score,
#             current_scores=current_scores,
#             decay_scores=decay_scores,
#             last_update_timestamp=last_update
#         )
        
#         # Validate calc_result
#         calc_result = max(0.0, min(100.0, calc_result))
        
#         print(f"calc_result: {calc_result:.2f}")
        
#         return {
#             "user_scores": updated_scores,
#             "user_decay_scores": updated_decay,
#             "last_update_timestamp": timestamp,
#             "calc_result": calc_result
#         }
#     except Exception as e:
#         print(f"calculator fail: {e}")
#         return {
#             "user_scores": state.get("user_scores", {}),
#             "user_decay_scores": state.get("user_decay_scores", {}),
#             "last_update_timestamp": state.get("last_update_timestamp"),
#             "calc_result": 0.0
#         }
def calculator_func(state: MainState) -> MainState:
    try:
        top_k_results = state.get("top_k_results", [])
        
        # Fix field names to match calculator expectations
        fixed_top_k = []
        for result in top_k_results:
            fixed_result = {
                "similarity_score": result["similarity"],
                "label": result["status"],                 
                "text": result["text"],
                "id": result["id"]
            }
            fixed_top_k.append(fixed_result)
        
        intensity_score = state.get("intensity_score", {
            "pos": 0.1, "neg": 0.8, "neu": 0.1,
            "context_type": "personal", "personal_relevance": 1.0
        })
        
        # DEBUG: Print inputs
        print(f"=== CALCULATOR INPUT DEBUG ===")
        print(f"Search results: {len(fixed_top_k)}")
        for result in fixed_top_k:
            print(f"  {result['label']}: sim={result['similarity_score']:.3f}")
        print(f"Sentiment: pos={intensity_score.get('pos', 0):.3f}, neg={intensity_score.get('neg', 0):.3f}")
        print(f"Context: {intensity_score.get('context_type', 'unknown')}")
        
        current_scores = state.get("user_scores")
        decay_scores = state.get("user_decay_scores") 
        last_update = state.get("last_update_timestamp")
        
        # TEMPORARY FIX: Override calculator config for testing
        original_config = calculator.config.copy()
        
        # More aggressive settings for debugging
        calculator.config.update({
            "query_decay_rate": 0.1,  # Reduced decay
            "similarity_threshold": 0.1,  # Lower threshold  
            "context_dampening": {
                "personal": 1.0,
                "general": 0.7,   # Increased from 0.3
                "question": 0.8,  # Increased from 0.4  
                "academic": 0.4   # Increased from 0.2
            },
            "sentiment_weight": 1.2,  # Increased impact
            "sentiment_impact": 3.0   # Higher sentiment-only impact
        })
        
        # Calculate updated scores
        updated_scores, updated_decay, timestamp, calc_result = calculator.calculate_scores(
            user_id="temp",
            top_k_results=fixed_top_k,
            intensity_score=intensity_score,
            current_scores=current_scores,
            decay_scores=decay_scores,
            last_update_timestamp=last_update
        )
        
        # Restore original config
        calculator.config = original_config
        
        print(f"=== CALCULATOR OUTPUT DEBUG ===")
        print(f"Updated scores: {updated_scores}")
        print(f"Calc result: {calc_result:.2f}")
        
        # Validate calc_result
        calc_result = max(0.0, min(100.0, calc_result))
        
        return {
            "user_scores": updated_scores,
            "user_decay_scores": updated_decay,
            "last_update_timestamp": timestamp,
            "calc_result": calc_result
        }
    except Exception as e:
        print(f"Calculator fail: {e}")
        import traceback
        traceback.print_exc()
        return {
            "user_scores": state.get("user_scores", {}),
            "user_decay_scores": state.get("user_decay_scores", {}),
            "last_update_timestamp": state.get("last_update_timestamp"),
            "calc_result": 0.0
        }

def warning_gen_flag(state: MainState) -> MainState:
    try:
        calc_result = state.get("calc_result", 0.0)
        user_scores = state.get("user_scores", {})
        
        if not user_scores:
            print("no warning - no scores")
            return {"warning_text": ""}
        
        # Check for critical conditions first (suicide risk)
        suicidal_score = user_scores.get("Suicidal", 0.0)
        if suicidal_score > 70.0:  # High suicide risk regardless of calc_result
            print(f"critical warning - suicidal: {suicidal_score:.1f}")
            return {"warning_text": f"Critical concern detected: Suicidal indicators ({suicidal_score:.1f}/100)"}
        
        # Standard threshold-based warning (lowered to 30 for better sensitivity)
        if calc_result >= 30.0:
            # Get concerning scores (excluding Normal, above 15/100)
            negative_scores = [
                (label, score) for label, score in user_scores.items() 
                if label != "Normal" and score > 15.0
            ]
            
            # Sort by highest scores and get top 2
            top_2 = sorted(negative_scores, key=lambda x: x[1], reverse=True)[:2]
            
            if len(top_2) >= 2:
                warning_text = f"Elevated indicators: {top_2[0][0]} ({top_2[0][1]:.1f}/100), {top_2[1][0]} ({top_2[1][1]:.1f}/100)"
            elif len(top_2) == 1:
                warning_text = f"Elevated indicators: {top_2[0][0]} ({top_2[0][1]:.1f}/100)"
            else:
                warning_text = "General concern detected"
            
            print(f"warning generated - calc: {calc_result:.1f}")
            return {"warning_text": warning_text}
        
        print("no warning generated")
        return {"warning_text": ""}
        
    except Exception as e:
        print(f"warning fail: {e}")
        return {"warning_text": ""}