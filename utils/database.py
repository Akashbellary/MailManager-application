import os
import logging
from pymongo import MongoClient
from pymongo.collection import Collection
from typing import Dict, List, Optional, Any
from bson import ObjectId

logger = logging.getLogger(__name__)

class Database:
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self.connect()
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            # Get MongoDB connection string from environment
            mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
            self._client = MongoClient(mongo_uri)
            self._db = self._client.email_triage_ai
            
            # Test connection
            self._client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            # For development, create a simple in-memory fallback
            self._db = None
    
    def get_collection(self, collection_name: str) -> Collection:
        """Get MongoDB collection"""
        if self._db is None:
            raise Exception("Database not connected")
        return self._db[collection_name]
    
    def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()

# Global database instance
db = Database()

def get_emails_collection() -> Collection:
    """Get emails collection"""
    return db.get_collection('emails')

def get_responses_collection() -> Collection:
    """Get responses collection"""
    return db.get_collection('responses')

def get_progress_collection() -> Collection:
    """Get upload progress collection"""
    return db.get_collection('upload_progress')

def convert_objectid(doc: Dict) -> Dict:
    """Convert ObjectId to string for JSON serialization"""
    if doc and '_id' in doc and isinstance(doc['_id'], ObjectId):
        doc['_id'] = str(doc['_id'])
    return doc

def convert_objectids(docs: List[Dict]) -> List[Dict]:
    """Convert ObjectIds to strings in a list of documents"""
    return [convert_objectid(doc) for doc in docs]

# Database operations
def insert_email(email_data: Dict) -> str:
    """Insert email document"""
    try:
        collection = get_emails_collection()
        result = collection.insert_one(email_data)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error inserting email: {e}")
        raise

def find_emails(filter_dict: Optional[Dict] = None, skip: int = 0, limit: int = 20, sort_field: str = 'created_at', sort_order: int = -1) -> List[Dict]:
    """Find emails with pagination"""
    try:
        collection = get_emails_collection()
        filter_dict = filter_dict or {}
        
        cursor = collection.find(filter_dict).sort(sort_field, sort_order).skip(skip).limit(limit)
        emails = list(cursor)
        return convert_objectids(emails)
    except Exception as e:
        logger.error(f"Error finding emails: {e}")
        return []

def count_emails(filter_dict: Optional[Dict] = None) -> int:
    """Count emails matching filter"""
    try:
        collection = get_emails_collection()
        filter_dict = filter_dict or {}
        return collection.count_documents(filter_dict)
    except Exception as e:
        logger.error(f"Error counting emails: {e}")
        return 0

def find_email_by_id(email_id: str) -> Optional[Dict]:
    """Find email by ID"""
    try:
        collection = get_emails_collection()
        email = collection.find_one({'_id': ObjectId(email_id)})
        return convert_objectid(email) if email else None
    except Exception as e:
        logger.error(f"Error finding email by ID: {e}")
        return None

def update_email(email_id: str, update_data: Dict) -> bool:
    """Update email document"""
    try:
        collection = get_emails_collection()
        result = collection.update_one(
            {'_id': ObjectId(email_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating email: {e}")
        return False

def insert_response(response_data: Dict) -> str:
    """Insert response document"""
    try:
        collection = get_responses_collection()
        result = collection.insert_one(response_data)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error inserting response: {e}")
        raise

def find_responses(filter_dict: Optional[Dict] = None, skip: int = 0, limit: int = 20) -> List[Dict]:
    """Find responses with pagination"""
    try:
        collection = get_responses_collection()
        filter_dict = filter_dict or {}
        
        cursor = collection.find(filter_dict).sort('created_at', -1).skip(skip).limit(limit)
        responses = list(cursor)
        return convert_objectids(responses)
    except Exception as e:
        logger.error(f"Error finding responses: {e}")
        return []

def find_response_by_id(response_id: str) -> Optional[Dict]:
    """Find response by ID"""
    try:
        collection = get_responses_collection()
        response = collection.find_one({'_id': ObjectId(response_id)})
        return convert_objectid(response) if response else None
    except Exception as e:
        logger.error(f"Error finding response by ID: {e}")
        return None

def update_response(response_id: str, update_data: Dict) -> bool:
    """Update response document"""
    try:
        collection = get_responses_collection()
        result = collection.update_one(
            {'_id': ObjectId(response_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating response: {e}")
        return False

def find_responses_by_email_id(email_id: str) -> List[Dict]:
    """Find responses for specific email"""
    try:
        collection = get_responses_collection()
        cursor = collection.find({'email_id': email_id}).sort('created_at', -1)
        responses = list(cursor)
        return convert_objectids(responses)
    except Exception as e:
        logger.error(f"Error finding responses by email ID: {e}")
        return []

# Progress tracking
def insert_progress(progress_data: Dict) -> str:
    """Insert upload progress document"""
    try:
        collection = get_progress_collection()
        result = collection.insert_one(progress_data)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error inserting progress: {e}")
        raise

def update_progress(progress_id: str, update_data: Dict) -> bool:
    """Update upload progress"""
    try:
        collection = get_progress_collection()
        result = collection.update_one(
            {'_id': ObjectId(progress_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating progress: {e}")
        return False

def find_progress_by_id(progress_id: str) -> Optional[Dict]:
    """Find progress by ID"""
    try:
        collection = get_progress_collection()
        progress = collection.find_one({'_id': ObjectId(progress_id)})
        return convert_objectid(progress) if progress else None
    except Exception as e:
        logger.error(f"Error finding progress by ID: {e}")
        return None
