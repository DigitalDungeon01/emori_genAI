import os
from typing import Dict, List, Optional
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer
import torch

_retriever_instance = None

class zilliz_retriever_b:
    
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
        
        self.client = MilvusClient(uri=self.uri, token=self.token)
        
        if not self.client.has_collection(self.collection_name):
            raise ValueError(f"Collection '{self.collection_name}' does not exist")
        
        device = 'cuda' if use_cuda and torch.cuda.is_available() else 'cpu'
        self.embedding_model = SentenceTransformer(embedding_model, device=device)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
    
    def query_to_embedding(self, query: str) -> List[float]:
        embedding = self.embedding_model.encode([query])
        return embedding[0].tolist()
    
    def _build_filter_expression(self, filters: Dict) -> str:
        if not filters:
            return None
        
        filter_conditions = []
        
        for field, values in filters.items():
            if field == 'filename':
                if isinstance(values, list):
                    filename_conditions = []
                    for filename in values:
                        filename_conditions.append(f'filename == "{filename}"')
                    if filename_conditions:
                        filter_conditions.append(f"({' or '.join(filename_conditions)})")
                else:
                    filter_conditions.append(f'filename == "{values}"')
            
            elif field == 'status':
                if isinstance(values, list):
                    status_conditions = []
                    for status in values:
                        status_conditions.append(f'status == "{status}"')
                    if status_conditions:
                        filter_conditions.append(f"({' or '.join(status_conditions)})")
                else:
                    filter_conditions.append(f'status == "{values}"')
            
            else:
                if isinstance(values, list):
                    field_conditions = []
                    for value in values:
                        field_conditions.append(f'{field} == "{value}"')
                    if field_conditions:
                        filter_conditions.append(f"({' or '.join(field_conditions)})")
                else:
                    filter_conditions.append(f'{field} == "{values}"')
        
        return " and ".join(filter_conditions) if filter_conditions else None
    
    def semantic_search_b(self,
                       query: str,
                       top_k: int,
                       filters: Optional[Dict] = None,
                       threshold: Optional[float] = None) -> List[Dict]:
        
        query_embedding = self.query_to_embedding(query)
        filter_expr = self._build_filter_expression(filters) if filters else None
        
        try:
            search_results = self.client.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                limit=top_k * 2,
                search_params={"metric_type": "COSINE", "params": {"level": 1}},
                output_fields=["id", "text", "chunk_id", "total_chunks", "chunk_index",
                             "status", "filename", "char_count", "timestamp"],
                filter=filter_expr
            )
            
            formatted_results = []
            
            for hits in search_results:
                for hit in hits:
                    similarity_score = float(hit.score)
                    
                    if threshold is not None and similarity_score < threshold:
                        continue
                    
                    result = {
                        'id': hit.entity.get('id'),
                        'similarity_score': similarity_score,
                        'text': hit.entity.get('text', ''),
                        'chunk_id': hit.entity.get('chunk_id'),
                        'total_chunks': hit.entity.get('total_chunks'),
                        'chunk_index': hit.entity.get('chunk_index'),
                        'status': hit.entity.get('status'),
                        'filename': hit.entity.get('filename'),
                        'char_count': hit.entity.get('char_count'),
                        'timestamp': hit.entity.get('timestamp')
                    }
                    
                    formatted_results.append(result)
            
            formatted_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return formatted_results[:top_k]
            
        except Exception as e:
            print(f"Search error: {e}")
            return []

def initialize_retriever_b(zilliz_uri: str, 
                        zilliz_token: str, 
                        collection_name: str, 
                        embedding_model: str = "all-MiniLM-L6-v2",
                        use_cuda: bool = True) -> str:
    
    if not zilliz_uri or not zilliz_token or not collection_name:
        return "Error: zilliz_uri, zilliz_token, and collection_name are required"
    
    global _retriever_instance
    try:
        _retriever_instance = zilliz_retriever_b(
            zilliz_uri=zilliz_uri,
            zilliz_token=zilliz_token, 
            collection_name=collection_name,
            embedding_model=embedding_model,
            use_cuda=use_cuda
        )
        return "Retriever initialized successfully"
    except Exception as e:
        return f"Initialization failed: {str(e)}"

def semantic_search_b(query: str, 
                   top_k: int, 
                   filters: Optional[Dict] = None,
                   threshold: Optional[float] = None) -> List[Dict]:
    
    if not query or not top_k:
        return [{"error": "query and top_k are required parameters"}]
    
    if _retriever_instance is None:
        return [{"error": "Retriever not initialized. Call initialize_retriever_b first"}]
    
    return _retriever_instance.semantic_search_b(query, top_k, filters, threshold)