import sys
import os
from dotenv import load_dotenv
load_dotenv()

sys.path.append('/app')
from shared.state import MainState
from shared.schemas import FilterCategory, DocumentGrade, GradingDocument
from llm_model.llm import llm_model
from database.milvus_cloud_db.zilliz_retriever import semantic_search, initialize_retriever
from bson import ObjectId
from services.crud  import create_mental_health_db

# Load environment variables
zilliz_uri = os.getenv("ZILLIZ_URI")
zilliz_token = os.getenv("ZILLIZ_TOKEN")

# Initialize retriever
initialize_retriever(
    zilliz_uri=zilliz_uri,
    zilliz_token=zilliz_token,
    collection_name= "mental_health_emori", # dont change this
    embedding_model= "all-MiniLM-L6-v2",
    use_cuda= False
)

#when LLM fails to grade a document:
GRADING_CONFIG = {
    "text_preview_length": 250, # controls how much document text is shown to the LLM for grading.
    "default_grade": 0 # Uses 70
}

def filter_generator_node(state: MainState) -> MainState:
    try:
        query = state["user_query"]
        
        prompt = (
            "Based on the user query, analyze and choose exactly ONE category from this list:\n"
            "- research\n"
            "- report\n"  
            "- conversation\n"
            "- article\n\n"
            f"Query: {query}\n\n"
            "Respond with only ONE word from the list above. No explanations, no other text."
        )
        
        llm_response = llm_model.with_structured_output(FilterCategory).invoke(prompt)
        filter_word = llm_response.category.lower()
        
        # Validate response
        allowed_categories = ["research", "report", "conversation", "article"]
        
        if filter_word in allowed_categories:
            print(f"filter generated: {filter_word}")
            return {"label": filter_word}
        else:
            print(f"invalid filter: {filter_word}, using fallback")
            return {"label": "conversation"}  # Safe fallback
            
    except Exception as e:
        print(f"filter generation failed: {e}")
        return {"label": "conversation"}  # Safe fallback

    
    
def semantic_search_a_node(state: MainState) -> MainState:
    try:
        query = state["user_query"]
        filter_value = state.get("label")  # Fixed field name
        
        filters = {"category": [filter_value]}
        semantic_result = semantic_search(query, top_k=15, filters=filters, threshold=0.0)
        
        result = [{'id': item['id'], 'text': item['text']} for item in semantic_result]
        
        if result:
            print(f"found {len(result)} results for {filter_value}")
        else:
            print("no search results found")
            
        return {"semantic_search_a_results": result}
        
    except Exception as e:
        print(f"search failed: {e}")
        return {"semantic_search_a_results": []}
    
    
def grading_document_node(state: MainState) -> MainState:
    try:
        query = state["user_query"]
        documents = state.get("semantic_search_a_results", [])
        
        if not documents:
            print("no documents to grade")
            return {"graded_documents": []}
        
        # Build concise prompt
        prompt = f"Rate document relevance to query (1-100):\nQuery: {query}\n\nDocuments:\n"
        
        for doc in documents:
            text_preview = doc['text'][:GRADING_CONFIG["text_preview_length"]]
            prompt += f"ID: {doc['id']}\nText: {text_preview}...\n\n"
        
        prompt += "Return grades for each document by ID."
        
        llm_response = llm_model.with_structured_output(GradingDocument).invoke(prompt)
        
        # Create grade mapping
        grade_map = {doc.id: doc.grade for doc in llm_response.grades}
        
        # Build final results with grades (no filtering yet)
        graded_docs = []
        for doc in documents:
            grade = grade_map.get(doc['id'], GRADING_CONFIG["default_grade"])
            graded_docs.append({
                "id": doc['id'],
                "text": doc['text'],
                "grade": grade
            })
        
        print(f"graded {len(graded_docs)} documents")
        
        return {"graded_documents": graded_docs}
        
    except Exception as e:
        print(f"grading failed: {e}")
        return {"graded_documents": []}

def filter_document_node(state: MainState) -> MainState:
    try:
        graded_documents = state.get("graded_documents", [])
        
        if not graded_documents:
            print("no documents to filter")
            return {"semantic_search_a_results": []}
        
        # Filter documents by threshold (built-in value)
        threshold = 50 #rops documents with grades < 75
        filtered_docs = []
        
        for doc in graded_documents:
            if doc.get("grade", 0) >= threshold:
                # Keep only id and text for final output
                filtered_docs.append({
                    "id": doc["id"],
                    "text": doc["text"]
                })
        
        print(f"filtered {len(filtered_docs)} from {len(graded_documents)} documents")
       
        
        return {"semantic_search_a_results": filtered_docs}
        
    except Exception as e:
        print(f"filtering failed: {e}")
        return {"semantic_search_a_results": []}
    
    
    
