import os
from pymongo import MongoClient
from bson import ObjectId
from typing import Dict, List, Optional

# Load from .env
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'emailclassifier')

# Increase timeouts to handle slow heartbeats/latency
client = MongoClient(
    os.environ.get('MONGODB_URI'),
    connectTimeoutMS=60000,  # 60 seconds
    socketTimeoutMS=60000,
    serverSelectionTimeoutMS=60000,
    heartbeatFrequencyMS=30000  # Increase heartbeat interval to reduce frequency of checks
)
db = client[MONGODB_DB_NAME]  # Use from .env

def get_emails_collection():
    return db['emails']

def get_responses_collection():
    return db['responses']

def get_progress_collection():
    return db['progress']

def insert_email(email_data: Dict):
    if '_id' not in email_data or email_data['_id'] is None:
        email_data['_id'] = ObjectId()
    return get_emails_collection().insert_one(email_data).inserted_id

def update_progress(progress_id: str, update_data: Dict):
    result = get_progress_collection().update_one({'_id': ObjectId(progress_id)}, {'$set': update_data})
    return result.modified_count > 0

def insert_progress(progress_data: Dict):
    result = get_progress_collection().insert_one(progress_data)
    return str(result.inserted_id)

def find_emails(query: Dict, skip: int = 0, limit: int = 0) -> List[Dict]:
    cursor = get_emails_collection().find(query).skip(skip)
    if limit > 0:
        cursor = cursor.limit(limit)
    return list(cursor)

def count_emails(query: Dict) -> int:
    return get_emails_collection().count_documents(query)

def find_email_by_id(email_id: str) -> Optional[Dict]:
    return get_emails_collection().find_one({'_id': ObjectId(email_id)})

def insert_response(response_data: Dict):
    if '_id' not in response_data or response_data['_id'] is None:
        response_data['_id'] = ObjectId()
    return get_responses_collection().insert_one(response_data).inserted_id

def find_responses(query: Dict, skip: int = 0, limit: int = 0) -> List[Dict]:
    cursor = get_responses_collection().find(query).skip(skip)
    if limit > 0:
        cursor = cursor.limit(limit)
    return list(cursor)

def find_responses_by_email_id(email_id: str) -> List[Dict]:
    return list(get_responses_collection().find({'email_id': email_id}))

def find_response_by_id(response_id: str) -> Optional[Dict]:
    return get_responses_collection().find_one({'_id': ObjectId(response_id)})

def update_response(response_id: str, update_data: Dict):
    result = get_responses_collection().update_one({'_id': ObjectId(response_id)}, {'$set': update_data})
    return result.modified_count > 0

def find_progress_by_id(progress_id: str) -> Optional[Dict]:
    return get_progress_collection().find_one({'_id': ObjectId(progress_id)})