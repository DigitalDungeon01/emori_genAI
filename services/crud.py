"""
Mental Health Chat Companion - MongoDB Database Module
Final version with optimized retrieve methods using get_fields() approach.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from bson import ObjectId
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import PyMongoError


class MentalHealthDB:
    """
    MongoDB module for Mental Health Chat Companion system.
    Uses MongoDB ObjectId as primary key and 'name' for user identification.
    Handles user data with APPEND pattern for conversations and OVERWRITE for metrics.
    """
    
    def __init__(self, connection_string: str, database_name: str = "mental_health_db", 
                 collection_name: str = "users"):
        """
        Initialize the MongoDB connection.
        
        Args:
            connection_string: MongoDB connection URI
            database_name: Name of the database
            collection_name: Name of the collection
        """
        self.client = MongoClient(connection_string)
        self.db: Database = self.client[database_name]
        self.collection: Collection = self.db[collection_name]
        self.logger = logging.getLogger(__name__)
        
        # Create index on name for faster queries (non-unique to allow duplicate names)
        self.collection.create_index("name")
    
    def create_user(self, name: str) -> Dict[str, Any]:
        """
        Create a new user with default values.
        
        Args:
            name: User's name (can be duplicate)
            
        Returns:
            Dict containing the created user document
        """
        new_user = {
            "name": name,
            "past_conversation": "[]",
            "user_scores": "null",
            "user_decay_scores": "null",
            "last_update_timestamp": None,
            "calc_result": None
        }
        
        result = self.collection.insert_one(new_user)
        new_user["_id"] = result.inserted_id
        return new_user
    
    def get_user(self, user_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by ObjectId.
        
        Args:
            user_id: MongoDB ObjectId (string or ObjectId object)
            
        Returns:
            User document or None if not found
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        return self.collection.find_one({"_id": user_id})
    
    def get_user_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Retrieve users by name (can return multiple users with same name).
        
        Args:
            name: User's name
            
        Returns:
            List of user documents
        """
        return list(self.collection.find({"name": name}))
    
    def get_latest_user_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recently created user with given name.
        
        Args:
            name: User's name
            
        Returns:
            Most recent user document or None if not found
        """
        user = self.collection.find({"name": name}).sort("_id", -1).limit(1)
        users = list(user)
        return users[0] if users else None
    
    def append_conversation(self, user_id: Union[str, ObjectId], user_query: str, answer: str, 
                          metadata: Optional[Dict] = None) -> bool:
        """
        Append a new conversation entry to the user's conversation history.
        Uses APPEND pattern - adds to existing conversation array.
        
        Args:
            user_id: MongoDB ObjectId (string or ObjectId object)
            user_query: User's question or message
            answer: System's response
            metadata: Optional additional data (sentiment, crisis_score, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        user = self.get_user(user_id)
        if not user:
            return False
        
        try:
            current_conversations = json.loads(user["past_conversation"])
        except json.JSONDecodeError:
            current_conversations = []
        
        new_conversation = {
            "user_query": user_query,
            "answer": answer,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if metadata:
            new_conversation.update(metadata)
        
        current_conversations.append(new_conversation)
        
        result = self.collection.update_one(
            {"_id": user_id},
            {"$set": {"past_conversation": json.dumps(current_conversations)}}
        )
        
        return result.modified_count > 0
    
    def update_user_scores(self, user_id: Union[str, ObjectId], scores: Dict[str, Any]) -> bool:
        """
        Update user scores (OVERWRITE pattern).
        Completely replaces the existing user_scores.
        
        Args:
            user_id: MongoDB ObjectId (string or ObjectId object)
            scores: Dictionary containing score data
            
        Returns:
            True if successful, False otherwise
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        result = self.collection.update_one(
            {"_id": user_id},
            {"$set": {"user_scores": json.dumps(scores)}}
        )
        return result.modified_count > 0
    
    def update_decay_scores(self, user_id: Union[str, ObjectId], decay_scores: Dict[str, Any]) -> bool:
        """
        Update user decay scores (OVERWRITE pattern).
        Completely replaces the existing user_decay_scores.
        
        Args:
            user_id: MongoDB ObjectId (string or ObjectId object)
            decay_scores: Dictionary containing decay score data
            
        Returns:
            True if successful, False otherwise
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        result = self.collection.update_one(
            {"_id": user_id},
            {"$set": {"user_decay_scores": json.dumps(decay_scores)}}
        )
        return result.modified_count > 0
    
    def update_timestamp(self, user_id: Union[str, ObjectId], timestamp: Optional[str] = None) -> bool:
        """
        Update last_update_timestamp (OVERWRITE pattern).
        
        Args:
            user_id: MongoDB ObjectId (string or ObjectId object)
            timestamp: ISO timestamp string, defaults to current UTC time
            
        Returns:
            True if successful, False otherwise
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        
        result = self.collection.update_one(
            {"_id": user_id},
            {"$set": {"last_update_timestamp": timestamp}}
        )
        return result.modified_count > 0
    
    def update_calc_result(self, user_id: Union[str, ObjectId], calc_result: Union[int, float]) -> bool:
        """
        Update calculation result (OVERWRITE pattern).
        
        Args:
            user_id: MongoDB ObjectId (string or ObjectId object)
            calc_result: Numerical calculation result
            
        Returns:
            True if successful, False otherwise
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        result = self.collection.update_one(
            {"_id": user_id},
            {"$set": {"calc_result": calc_result}}
        )
        return result.modified_count > 0
    
    def update_name(self, user_id: Union[str, ObjectId], new_name: str) -> bool:
        """
        Update user's name (OVERWRITE pattern).
        
        Args:
            user_id: MongoDB ObjectId (string or ObjectId object)
            new_name: New name for the user
            
        Returns:
            True if successful, False otherwise
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        result = self.collection.update_one(
            {"_id": user_id},
            {"$set": {"name": new_name}}
        )
        return result.modified_count > 0
    
    def bulk_update_user(self, user_id: Union[str, ObjectId], updates: Dict[str, Any]) -> bool:
        """
        Perform multiple updates in a single operation (OVERWRITE pattern only).
        Note: This does NOT append to conversations - use append_conversation() for that.
        
        Args:
            user_id: MongoDB ObjectId (string or ObjectId object)
            updates: Dictionary with fields to update
                    Valid keys: name, user_scores, user_decay_scores, last_update_timestamp, calc_result
        
        Returns:
            True if successful, False otherwise
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        allowed_fields = {"name", "user_scores", "user_decay_scores", "last_update_timestamp", "calc_result"}
        filtered_updates = {}
        
        for key, value in updates.items():
            if key in allowed_fields:
                if key in ["user_scores", "user_decay_scores"] and isinstance(value, dict):
                    filtered_updates[key] = json.dumps(value)
                else:
                    filtered_updates[key] = value
        
        if not filtered_updates:
            return False
        
        result = self.collection.update_one(
            {"_id": user_id},
            {"$set": filtered_updates}
        )
        return result.modified_count > 0
    
    def get_fields(self, user_id: Union[str, ObjectId], *fields) -> Any:
        """
        Get specific fields from user document.
        
        Args:
            user_id: MongoDB ObjectId (string or ObjectId object)
            *fields: Field names to retrieve
        
        Returns:
            Single value if one field, dict if multiple fields, None if user not found
        """
        user = self.get_user(user_id)
        if not user:
            return None
        
        if len(fields) == 1:
            return user.get(fields[0])
        
        return {field: user.get(field) for field in fields}
    
    def get_bulk_data(self, user_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        """
        Get complete user document.
        
        Args:
            user_id: MongoDB ObjectId (string or ObjectId object)
            
        Returns:
            Complete user document or None if not found
        """
        return self.get_user(user_id)
    
    def get_conversation_history(self, user_id: Union[str, ObjectId]) -> List[Dict[str, Any]]:
        """
        Get parsed conversation history for a user.
        
        Args:
            user_id: MongoDB ObjectId (string or ObjectId object)
            
        Returns:
            List of conversation dictionaries
        """
        user = self.get_user(user_id)
        if not user:
            return []
        
        try:
            conversations = json.loads(user["past_conversation"])
            return conversations if isinstance(conversations, list) else []
        except json.JSONDecodeError:
            return []
    
    def get_user_scores(self, user_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        """
        Get parsed user scores.
        
        Args:
            user_id: MongoDB ObjectId (string or ObjectId object)
            
        Returns:
            Dictionary of scores or None
        """
        user = self.get_user(user_id)
        if not user or user["user_scores"] == "null":
            return None
        
        try:
            return json.loads(user["user_scores"])
        except json.JSONDecodeError:
            return None
    
    def get_decay_scores(self, user_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        """
        Get parsed decay scores.
        
        Args:
            user_id: MongoDB ObjectId (string or ObjectId object)
            
        Returns:
            Dictionary of decay scores or None
        """
        user = self.get_user(user_id)
        if not user or user["user_decay_scores"] == "null":
            return None
        
        try:
            return json.loads(user["user_decay_scores"])
        except json.JSONDecodeError:
            return None
    
    def delete_user(self, user_id: Union[str, ObjectId]) -> bool:
        """
        Delete a user completely.
        
        Args:
            user_id: MongoDB ObjectId (string or ObjectId object)
            
        Returns:
            True if successful, False otherwise
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        result = self.collection.delete_one({"_id": user_id})
        return result.deleted_count > 0
    
    def list_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users in the database.
        
        Returns:
            List of all user documents
        """
        return list(self.collection.find())
    
    def search_users(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search users by custom query.
        
        Args:
            query: MongoDB query dictionary
            
        Returns:
            List of matching user documents
        """
        return list(self.collection.find(query))
    
    def close_connection(self):
        """Close the MongoDB connection."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_connection()


def create_mental_health_db(connection_string: str, database_name: str = "mental_health_db") -> MentalHealthDB:
    """
    Factory function to create a MentalHealthDB instance.
    
    Args:
        connection_string: MongoDB connection URI
        database_name: Name of the database
        
    Returns:
        MentalHealthDB instance
    """
    return MentalHealthDB(connection_string, database_name)