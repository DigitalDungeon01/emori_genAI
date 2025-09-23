from typing import Dict, List
from sentence_transformers import SentenceTransformer
import numpy as np
import torch

class embedding:
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2", use_cuda: bool = True):
        # Device setup
        if use_cuda and torch.cuda.is_available():
            self.device = 'cuda'
            print(f"Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            self.device = 'cpu'
            print("Using CPU for embeddings")
        
        # Load model
        print(f"Loading model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model, device=self.device)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        self.model_name = embedding_model
        
        print(f"Model loaded. Dimension: {self.embedding_dim}")
    
    def generate_embeddings(self, text_list: List[str], batch_size: int = 32) -> np.ndarray:
        if not text_list:
            return np.array([])
        
        print(f"Generating embeddings for {len(text_list)} texts")
        
        all_embeddings = []
        for i in range(0, len(text_list), batch_size):
            batch_texts = text_list[i:i + batch_size]
            batch_embeddings = self.embedding_model.encode(
                batch_texts,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            all_embeddings.append(batch_embeddings)
        
        return np.vstack(all_embeddings) if all_embeddings else np.array([])
    
    def process_chunks(self, processed_chunks: List[Dict]) -> List[Dict]:
        if not processed_chunks:
            raise ValueError("No processed_chunks provided")
        
        print(f"Processing {len(processed_chunks)} chunks for embedding")
        
        # Extract texts and generate embeddings
        texts_for_embedding = [chunk['text'] for chunk in processed_chunks]
        embeddings = self.generate_embeddings(texts_for_embedding)
        
        # Add embeddings to chunks
        embedded_chunks = []
        for i, chunk in enumerate(processed_chunks):
            embedded_chunk = chunk.copy()
            embedded_chunk['embedding'] = embeddings[i].tolist()
            embedded_chunks.append(embedded_chunk)
        
        print(f"Generated {len(embedded_chunks)} embeddings")
        return embedded_chunks
    
    def show_embedding_info(self, embedded_chunks: List[Dict]):
        if not embedded_chunks:
            print("No embedded chunks to show")
            return
        
        # Basic info
        print(f"Total chunks: {len(embedded_chunks)}")
        print(f"Model: {self.model_name}")
        print(f"Embedding dimension: {self.embedding_dim}")
        print(f"Device: {self.device}")
        
        # Content stats
        avg_content_len = np.mean([len(chunk['text']) for chunk in embedded_chunks])
        print(f"Average content length: {avg_content_len:.1f} characters")
        
        # Sample from first chunk
        first_chunk = embedded_chunks[0]
        print(f"Content: {first_chunk['text'][:100]}...")
        print(f"Embedding preview: {first_chunk['embedding'][:5]}")
        print(f"Full embedding length: {len(first_chunk['embedding'])}")
        
        # Metadata sample
        metadata = first_chunk.get('metadata', {})
        print(f"Metadata: chunk_id={metadata.get('chunk_id')}")
    
    def show_raw_embeddings(self, embedded_chunks: List[Dict], max_chunks: int = 2):
        if not embedded_chunks:
            print("No embedded chunks to show")
            return
        
        for i, chunk in enumerate(embedded_chunks[:max_chunks]):
            print(f"Chunk {i+1}:")
            print(f"Content: {chunk['text'][:80]}...")
            print(f"Raw embedding vector:")
            print(chunk['embedding'])
            print("-" * 40)
        
        if len(embedded_chunks) > max_chunks:
            print(f"... and {len(embedded_chunks) - max_chunks} more chunks")