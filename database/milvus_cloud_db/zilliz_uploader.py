import os
import json
from typing import Dict, List, Optional
from pymilvus import MilvusClient, DataType

class zilliz_uploader:
    
    def __init__(self, 
                 zilliz_uri: str,
                 zilliz_token: str,
                 collection_name: str = "knowledge_base",
                 embedding_dim: int = 384):
        
        # Get credentials from parameters or environment variables
        self.uri = zilliz_uri or os.getenv('MILVUS_URI')
        self.token = zilliz_token or os.getenv('MILVUS_TOKEN')
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        
        if not self.uri or not self.token:
            raise ValueError("Zilliz URI and token must be provided via parameters or environment variables")
        
        # Initialize client
        print(f"Connecting to Zilliz Cloud: {self.uri}")
        self.client = MilvusClient(uri=self.uri, token=self.token)
        print("Successfully connected to Zilliz Cloud")
        
        # Setup collection
        self._setup_collection()
    
    def _create_collection_schema(self):
        schema = self.client.create_schema()
        
        # Core fields
        schema.add_field("id", DataType.VARCHAR, max_length=200, is_primary=True)
        schema.add_field("text", DataType.VARCHAR, max_length=65535)
        schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=self.embedding_dim)
        
        # Metadata fields
        schema.add_field("chunk_id", DataType.VARCHAR, max_length=100)
        schema.add_field("total_chunks", DataType.INT64)
        schema.add_field("chunk_index", DataType.INT64)
        schema.add_field("char_count", DataType.INT64)
        schema.add_field("timestamp", DataType.INT64)
        schema.add_field("title", DataType.VARCHAR, max_length=500)
        schema.add_field("tags", DataType.VARCHAR, max_length=1000)
        schema.add_field("category", DataType.VARCHAR, max_length=500)
        schema.add_field("filename", DataType.VARCHAR, max_length=255)
        
        return schema
    
    def _setup_collection(self):
        if self.client.has_collection(self.collection_name):
            print(f"Collection '{self.collection_name}' already exists")
            return
        
        schema = self._create_collection_schema()
        
        index_params = self.client.prepare_index_params()
        index_params.add_index("embedding", metric_type="COSINE")
        
        self.client.create_collection(
            collection_name=self.collection_name,
            schema=schema,
            index_params=index_params
        )
        
        print(f"Created collection '{self.collection_name}' with schema")
    
    def _convert_chunk_to_zilliz_format(self, chunk: Dict) -> Dict:
        # Extract metadata
        metadata = chunk.get('metadata', {})
        
        # Generate unique ID using chunk_id
        chunk_id = metadata.get('chunk_id', 'unknown')
        unique_id = f"id_{chunk_id}"
        
        # Convert arrays to JSON strings for storage
        tags = metadata.get('tags', [])
        category = metadata.get('category', [])
        
        tags_json = json.dumps(tags) if isinstance(tags, list) else str(tags)
        category_json = json.dumps(category) if isinstance(category, list) else str(category)
        
        # Build Zilliz data
        zilliz_data = {
            'id': unique_id,
            'text': chunk['text'],
            'embedding': chunk['embedding'],
            'chunk_id': str(chunk_id),
            'total_chunks': metadata.get('total_chunks', 1),
            'chunk_index': metadata.get('chunk_index', 0),
            'char_count': metadata.get('char_count', 0),
            'timestamp': metadata.get('timestamp', 0),
            'title': metadata.get('title', ''),
            'tags': tags_json,
            'category': category_json,
            'filename': metadata.get('filename', '')
        }
        
        return zilliz_data
    
    def upload_chunks(self, embedded_chunks: List[Dict], batch_size: int = 100) -> Dict:
        if not embedded_chunks:
            raise ValueError("No embedded chunks to upload")
        
        print(f"Uploading {len(embedded_chunks)} chunks to collection '{self.collection_name}'")
        
        # Convert chunks to Zilliz format
        zilliz_data = []
        for chunk in embedded_chunks:
            try:
                converted_chunk = self._convert_chunk_to_zilliz_format(chunk)
                zilliz_data.append(converted_chunk)
            except Exception as e:
                print(f"Error converting chunk: {e}")
                continue
        
        if not zilliz_data:
            raise ValueError("No valid chunks to upload")
        
        try:
            total_uploaded = 0
            
            # Upload in batches
            for i in range(0, len(zilliz_data), batch_size):
                batch = zilliz_data[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(zilliz_data) + batch_size - 1) // batch_size
                
                print(f"Uploading batch {batch_num}/{total_batches} ({len(batch)} chunks)")
                
                self.client.insert(self.collection_name, batch)
                total_uploaded += len(batch)
            
            result = {
                'uploaded_count': total_uploaded,
                'collection_name': self.collection_name,
                'status': 'success'
            }
            
            print(f"Successfully uploaded {total_uploaded} chunks")
            return result
            
        except Exception as e:
            print(f"Error uploading chunks: {e}")
            return {
                'uploaded_count': 0,
                'status': 'failed',
                'error': str(e)
            }
    
    def get_collection_stats(self) -> Dict:
        try:
            stats = self.client.get_collection_stats(self.collection_name)
            
            return {
                'collection_name': self.collection_name,
                'total_entities': stats.get('row_count', 0),
                'embedding_dimension': self.embedding_dim
            }
            
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {'error': str(e)}
    
    def test_connection(self) -> bool:
        try:
            results = self.client.query(
                collection_name=self.collection_name,
                filter="timestamp >= 0",
                output_fields=["id", "filename"],
                limit=1
            )
            
            print(f"Connection test successful. Collection has {len(results)} or more entities.")
            return True
            
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def drop_collection(self):
        try:
            if self.client.has_collection(self.collection_name):
                self.client.drop_collection(self.collection_name)
                print(f"Dropped collection: {self.collection_name}")
            else:
                print(f"Collection {self.collection_name} does not exist")
        except Exception as e:
            print(f"Error dropping collection: {e}")