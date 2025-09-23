import sys
import os
sys.path.append('/app')

from shared.state import MainState
from shared.schemas import EvaluationResponse
from llm_model.llm import llm_model
from services.crud import create_mental_health_db
from config import get_database_config
from bson import ObjectId

MAX_RETRIES = 2 # for evaluator

def load_memory_node(state: MainState) -> MainState:
    try:
        user_id = state.get("user_id")
        
        if not user_id:
            print("no user_id provided")
            return {
                "past_conversation": [],
                "user_scores": None,
                "user_decay_scores": None,
                "last_update_timestamp": None,
                "calc_result": None
            }
        
        # Convert to ObjectId if string
        if isinstance(user_id, str):
            user_id = ObjectId(user_id.strip())
        
        config = get_database_config()
        with create_mental_health_db(config["connection"], config["database"]) as db:
            user = db.get_user(user_id)
            
            if user:
                # Load existing user data
                past_conversation = db.get_conversation_history(user_id) or []
                user_scores = db.get_user_scores(user_id)
                user_decay_scores = db.get_decay_scores(user_id)
                
                print(f"loaded data for user: {user_id}")
                
                return {
                    "past_conversation": past_conversation,
                    "user_scores": user_scores,
                    "user_decay_scores": user_decay_scores,
                    "last_update_timestamp": user.get("last_update_timestamp"),
                    "calc_result": user.get("calc_result")
                }
            else:
                # New user
                print(f"new user: {user_id}")
                return {
                    "past_conversation": [],
                    "user_scores": None,
                    "user_decay_scores": None,
                    "last_update_timestamp": None,
                    "calc_result": None
                }
                
    except Exception as e:
        print(f"load failed: {e}")
        return {
            "past_conversation": [],
            "user_scores": None,
            "user_decay_scores": None,
            "last_update_timestamp": None,
            "calc_result": None
        }


def merge_path_AandB_node(state: MainState) -> MainState:
    # Check what data we have from both paths
    path_a_results = state.get("semantic_search_a_results", [])
    path_b_results = state.get("semantic_search_b_results", [])
    
    # Simple status reporting
    if path_a_results and path_b_results:
        print("MERGED!")
    elif path_a_results:
        print("Path A received")
    elif path_b_results:
        print("Path B received")
    else:
        print("Not received")
    
    # Simple passthrough - no new fields needed
    # All data already exists in state from both subgraphs
    return {}


def answer_generator_node(state: MainState) -> MainState:
    try:
        user_query = state.get("user_query", "")
        path_a_results = state.get("semantic_search_a_results", [])
        warning_text = state.get("warning_text", "")
        evaluation_feedback = state.get("evaluation_feedback", "")
        past_conversation = state.get("past_conversation", [])
        
        # Configuration variables
        TEMPERATURE = 0.3
        MAX_TOKENS = 350
        
        # Build context only from PATH A results (graded documents)
        context_sources = []
        for doc in path_a_results:
            context_sources.append(doc.get("text", ""))
        
        # Handle no context case
        if not context_sources:
            print("no context available")
            return {
                "answer": "I understand you're reaching out for support. While I'm experiencing some technical difficulties right now, I want you to know that your concerns are valid. If you're in immediate distress, please contact a mental health professional or crisis helpline. Otherwise, please try again in a few moments."
            }
        
        # Build context text from Path A only
        context_text = "\n".join([f"- {source[:200]}..." for source in context_sources])
        
        # Add conversation history (last 3 exchanges)
        conversation_context = ""
        if past_conversation:
            recent_conversations = past_conversation[-3:]
            conversation_context = ""
            for conv in recent_conversations:
                conversation_context += f"User: {conv.get('user_query', '')[:100]}...\n"
                conversation_context += f"AI: {conv.get('answer', '')[:100]}...\n"
        
        # Add feedback if available
        feedback_section = ""
        if evaluation_feedback:
            feedback_section = f"\n\nImprove based on feedback: {evaluation_feedback}"
        
        # Improved prompt - Path A for context, Path B for warning only
        prompt = (
            f"You are a mental health support AI. Provide compassionate, evidence-based guidance.\n\n"
            f"USER'S CURRENT QUESTION:\n{user_query}\n\n"
            f"RETRIEVED CONTEXT INFORMATION:\nHere is relevant information I gathered from my knowledge base to help answer this question:\n{context_text}\n\n"
            f"CONVERSATION HISTORY:\nHere are the user's past conversations with you - use this context to maintain continuity and understand their ongoing concerns:\n{conversation_context}\n\n"
            f"MENTAL HEALTH ASSESSMENT:\n{warning_text if warning_text else 'No specific concerns detected'}{feedback_section}\n\n"
            f"Based on the current question, retrieved context information, and conversation history above, provide a supportive response that."
            # f"- Directly addresses their current question using the context provided\n"
            # f"- Uses warm, empathetic language\n"
            # f"- References relevant information from the retrieved context\n"
            # f"- Considers their conversation history for continuity\n"
            # f"- Includes practical coping strategies when relevant\n"
            # f"- Acknowledges any mental health concerns sensitively\n"
            # f"- Reminds user this is supportive information, not professional therapy\n"
            # f"- Maintains professional boundaries while being compassionate"
        )
        
        # LLM with temperature and token control
        limited_llm = llm_model.bind(
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        
        llm_response = limited_llm.invoke(prompt)
        answer = llm_response.content.strip()
        
        print(f"answer generated: {len(answer)} chars")
        
        return {"answer": answer}
        
    except Exception as e:
        print(f"answer generation failed: {e}")
        return {
            "answer": "I understand you're reaching out for support. While I'm experiencing some technical difficulties right now, I want you to know that your concerns are valid. If you're in immediate distress, please contact a mental health professional or crisis helpline. Otherwise, please try again in a few moments."
        }

def evaluator_node(state: MainState) -> MainState:
    try:
        user_query = state.get("user_query", "")
        answer = state.get("answer", "")
        
        # Simple retry tracking (since MainState doesn't have retry counter)
        evaluation_feedback = state.get("evaluation_feedback", "")
        current_attempt = 1 if not evaluation_feedback else 2
        
        prompt = (
            f"Evaluate this mental health AI response (score 0-100):\n\n"
            f"User query: {user_query}\n"
            f"AI response: {answer}\n\n"
            f"Score based on: empathy, safety, relevance, professionalism\n"
            f"Deduct for: medical advice, inappropriate tone, harmful content\n"
            f"If score below 75 , provide brief improvement feedback."
        )
        
        llm_response = llm_model.with_structured_output(EvaluationResponse).invoke(prompt)
        
        score = llm_response.score
        feedback = llm_response.feedback if score < 60 else ""
        
        # Decision logic
        
        if score >= 60:
            print(f"evaluation passed: {score}")
            return {
                "evaluation_result": "ok",
                "evaluation_feedback": ""
            }
        elif current_attempt >= MAX_RETRIES:
            print(f"evaluation failed but max retries reached: {score}")
            return {
                "evaluation_result": "ok",  # Accept to avoid infinite loop
                "evaluation_feedback": ""
            }
        else:
            print(f"evaluation failed, retry: {score}")
            return {
                "evaluation_result": "Not ok",
                "evaluation_feedback": feedback
            }
            
    except Exception as e:
        print(f"evaluation failed: {e}")
        return {
            "evaluation_result": "ok",  # Fail-safe to continue
            "evaluation_feedback": ""
        }
        

def save_memory_node(state: MainState) -> MainState:
    try:
        user_id = state.get("user_id")
        user_query = state.get("user_query", "")
        answer = state.get("answer", "")
        
        if not user_id:
            print("no user_id to save")
            return {}
        
        # Convert to ObjectId if string
        if isinstance(user_id, str):
            user_id = ObjectId(user_id.strip())
        
        config = get_database_config()
        with create_mental_health_db(config["connection"], config["database"]) as db:
            # Save conversation (APPEND pattern)
            conversation_saved = db.append_conversation(user_id, user_query, answer)
            
            # Prepare data for bulk update (OVERWRITE pattern)  
            update_data = {}
            if state.get("user_scores") is not None:
                update_data["user_scores"] = state.get("user_scores")
            if state.get("user_decay_scores") is not None:
                update_data["user_decay_scores"] = state.get("user_decay_scores") 
            if state.get("last_update_timestamp") is not None:
                update_data["last_update_timestamp"] = state.get("last_update_timestamp")
            if state.get("calc_result") is not None:
                update_data["calc_result"] = state.get("calc_result")
            
            # Save metrics data
            metrics_saved = db.bulk_update_user(user_id, update_data) if update_data else True
            
            if conversation_saved and metrics_saved:
                print(f"memory saved for user: {user_id}")
            else:
                print(f"partial save for user: {user_id}")
            
            return {}
            
    except Exception as e:
        print(f"memory save failed: {e}")
        return {}