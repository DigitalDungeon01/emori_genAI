import os
import json
from typing import Dict, List, Optional, Union
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer
import torch

# Global retriever instance
_retriever_instance = None

# Simple Zilliz Retriever Class
class zilliz_retriever:
    
    # Initialize retriever with connection and embedding model
    def __init__(self,
                 zilliz_uri: str,
                 zilliz_token: str,
                 collection_name: str,
                 embedding_model: str = "all-MiniLM-L6-v2",
                 use_cuda: bool = True):
        
        self.uri = zilliz_uri
        self.token = zilliz_token
        self.collection_name = collection_name
        
        if not self.uri or not self.token:
            raise ValueError("Zilliz URI and token must be provided")
        
        # Initialize Zilliz client
        self.client = MilvusClient(uri=self.uri, token=self.token)
        
        # Check collection exists
        if not self.client.has_collection(self.collection_name):
            raise ValueError(f"Collection '{self.collection_name}' does not exist")
        
        # Initialize embedding model
        device = 'cuda' if use_cuda and torch.cuda.is_available() else 'cpu'
        self.embedding_model = SentenceTransformer(embedding_model, device=device)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
    
    # Convert query to embedding vector
    def query_to_embedding(self, query: str) -> List[float]:
        embedding = self.embedding_model.encode([query])
        return embedding[0].tolist()
    
    # Build filter expression from filter dictionary
    def _build_filter_expression(self, filters: Dict) -> str:
        if not filters:
            return None
        
        filter_conditions = []
        
        for field, values in filters.items():
            if field in ['tags', 'category']:
                # Handle array fields stored as JSON strings
                if isinstance(values, list):
                    # For multiple values, create OR conditions
                    or_conditions = []
                    for value in values:
                        or_conditions.append(f'{field} like "%{value}%"')
                    if or_conditions:
                        filter_conditions.append(f"({' or '.join(or_conditions)})")
                else:
                    # Single value
                    filter_conditions.append(f'{field} like "%{values}%"')
            
            elif field == 'filename':
                if isinstance(values, list):
                    # Multiple filenames
                    filename_conditions = []
                    for filename in values:
                        filename_conditions.append(f'filename == "{filename}"')
                    if filename_conditions:
                        filter_conditions.append(f"({' or '.join(filename_conditions)})")
                else:
                    # Single filename
                    filter_conditions.append(f'filename == "{values}"')
            
            elif field == 'title':
                if isinstance(values, list):
                    # Multiple titles
                    title_conditions = []
                    for title in values:
                        title_conditions.append(f'title == "{title}"')
                    if title_conditions:
                        filter_conditions.append(f"({' or '.join(title_conditions)})")
                else:
                    # Single title
                    filter_conditions.append(f'title == "{values}"')
            
            else:
                # Handle other fields as exact matches
                if isinstance(values, list):
                    field_conditions = []
                    for value in values:
                        field_conditions.append(f'{field} == "{value}"')
                    if field_conditions:
                        filter_conditions.append(f"({' or '.join(field_conditions)})")
                else:
                    filter_conditions.append(f'{field} == "{values}"')
        
        return " and ".join(filter_conditions) if filter_conditions else None
    
    # Main semantic search function
    def semantic_search(self,
                       query: str,
                       top_k: int,
                       filters: Optional[Dict] = None,
                       threshold: Optional[float] = None) -> List[Dict]:
        
        # Convert query to embedding
        query_embedding = self.query_to_embedding(query)
        
        # Build filter expression
        filter_expr = self._build_filter_expression(filters) if filters else None
        
        try:
            # Perform vector search
            search_results = self.client.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                limit=top_k * 2,  # Get extra results for threshold filtering
                search_params={"metric_type": "COSINE", "params": {"level": 1}},
                output_fields=["id", "text", "chunk_id", "total_chunks", "chunk_index",
                             "title", "tags", "category", "filename", "char_count", "timestamp"],
                filter=filter_expr
            )
            
            # Format and filter results
            formatted_results = []
            
            for hits in search_results:
                for hit in hits:
                    similarity_score = float(hit.score)
                    
                    # Apply threshold filter
                    if threshold is not None and similarity_score < threshold:
                        continue
                    
                    # Parse category and tags from JSON strings
                    try:
                        category = json.loads(hit.entity.get('category', '[]'))
                        tags = json.loads(hit.entity.get('tags', '[]'))
                    except:
                        category = hit.entity.get('category', '')
                        tags = hit.entity.get('tags', '')
                    
                    result = {
                        'id': hit.entity.get('id'),
                        'similarity_score': similarity_score,
                        'text': hit.entity.get('text', ''),
                        'chunk_id': hit.entity.get('chunk_id'),
                        'total_chunks': hit.entity.get('total_chunks'),
                        'chunk_index': hit.entity.get('chunk_index'),
                        'title': hit.entity.get('title'),
                        'tags': tags,
                        'category': category,
                        'filename': hit.entity.get('filename'),
                        'char_count': hit.entity.get('char_count'),
                        'timestamp': hit.entity.get('timestamp')
                    }
                    
                    formatted_results.append(result)
            
            # Sort by similarity score and return top_k
            formatted_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return formatted_results[:top_k]
            
        except Exception as e:
            print(f"Search error: {e}")
            return []

# Global initialization function
def initialize_retriever(zilliz_uri: str, 
                        zilliz_token: str, 
                        collection_name: str, 
                        embedding_model: str = "all-MiniLM-L6-v2",
                        use_cuda: bool = True) -> str:
    
    # Validate parameters
    if not zilliz_uri or not zilliz_token or not collection_name:
        return "Error: zilliz_uri, zilliz_token, and collection_name are required"
    
    global _retriever_instance
    try:
        _retriever_instance = zilliz_retriever(
            zilliz_uri=zilliz_uri,
            zilliz_token=zilliz_token, 
            collection_name=collection_name,
            embedding_model=embedding_model,
            use_cuda=use_cuda
        )
        return "Retriever initialized successfully"
    except Exception as e:
        return f"Initialization failed: {str(e)}"

# Main search function - only function needed for usage
def semantic_search(query: str, 
                   top_k: int, 
                   filters: Optional[Dict] = None,
                   threshold: Optional[float] = None) -> List[Dict]:
    
    # Validate parameters
    if not query or not top_k:
        return [{"error": "query and top_k are required parameters"}]
    
    # Check if retriever initialized
    if _retriever_instance is None:
        return [{"error": "Retriever not initialized. Call initialize_retriever first"}]
    
    return _retriever_instance.semantic_search(query, top_k, filters, threshold)