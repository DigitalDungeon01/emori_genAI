import re
from typing import Dict, List
from datetime import datetime


class text_processing:
    def __init__(self, chunk_size: int = 500, overlap_size: int = 50):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size

    # Split text into chunks with overlap
    def create_text_chunks(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]

        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            word_len = len(word) + 1  # +1 for space
            if current_length + word_len > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))

                # Overlap
                overlap_words = (
                    current_chunk[-self.overlap_size:]
                    if len(current_chunk) > self.overlap_size
                    else current_chunk
                )
                current_chunk = overlap_words + [word]
                current_length = sum(len(w) + 1 for w in current_chunk)
            else:
                current_chunk.append(word)
                current_length += word_len

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    # Process output from data_processing.py
    def process(self, processed_data: List[Dict]) -> List[Dict]:
        if not processed_data:
            raise ValueError("No processed_data provided")

        results = []
        
        for doc_idx, item in enumerate(processed_data):
            text = item.get("text", "").strip()
            metadata = item.get("metadata", {}).copy()

            chunks = self.create_text_chunks(text)
            total_chunks = len(chunks)

            for chunk_idx, chunk in enumerate(chunks):
                if len(chunk.strip()) < 20:
                    continue

                # Generate chunk_id based on category
                if 'category' in metadata and 'conversation' in metadata['category']:
                    chunk_id = f"conv_doc{doc_idx}_chunk{chunk_idx}"
                else:
                    chunk_id = f"doc{doc_idx}_chunk{chunk_idx}"

                new_metadata = metadata.copy()
                new_metadata.update({
                    'chunk_id': chunk_id,
                    'total_chunks': total_chunks,
                    'chunk_index': chunk_idx,
                    'char_count': len(chunk),
                    'timestamp': int(datetime.now().timestamp()),
                })

                results.append({
                    'text': chunk,
                    'metadata': new_metadata,
                })

        print(f"Processed {len(results)} text chunks from {len(processed_data)} source documents")
        return results