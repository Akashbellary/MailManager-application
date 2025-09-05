import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from pymongo.collection import Collection
    from pymongo.database import Database
    from bson import ObjectId
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    # Create dummy classes for when PyMongo is not available
    class MongoClient:
        pass
    class Collection:
        pass
    class Database:
        pass
    class ObjectId:
        def __init__(self, *args, **kwargs):
            import uuid
            self._id = str(uuid.uuid4())
        def __str__(self):
            return self._id
    ASCENDING = 1
    DESCENDING = -1

from models import EmailRecord, DraftResponse

logger = logging.getLogger(__name__)

class MongoDBService:
    """MongoDB service for email storage and retrieval with vector search"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.emails_collection: Optional[Collection] = None
        self.responses_collection: Optional[Collection] = None
    
    def connect(self):
        """Connect to MongoDB"""
        if not PYMONGO_AVAILABLE:
            logger.warning("PyMongo not available, using in-memory storage")
            self.client = None
            self.db = None
            self.emails_collection = None
            self.responses_collection = None
            # Initialize in-memory storage
            self._memory_storage = []
            self._memory_responses = []
            return
            
        try:
            mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/emailclassifier")
            db_name = os.getenv("MONGODB_DB_NAME", "emailclassifier")
            
            self.client = MongoClient(mongodb_uri)
            self.db = self.client[db_name]
            self.emails_collection = self.db.emails
            self.responses_collection = self.db.draft_responses
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
            # Create indexes
            self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            # Don't raise, use in-memory storage instead
            self.client = None
            self.db = None
            self.emails_collection = None
            self.responses_collection = None
            self._memory_storage = []
            self._memory_responses = []
            logger.info("Using in-memory storage as fallback")
    
    def _create_indexes(self):
        """Create necessary indexes including vector search index"""
        if self.emails_collection is None:
            return
            
        try:
            # Index on metadata.date_epoch for date sorting
            self.emails_collection.create_index([("metadata.date_epoch", DESCENDING)])
            
            # Compound index for common filters
            self.emails_collection.create_index([
                ("priority", ASCENDING),
                ("sentiment", ASCENDING),
                ("classification", ASCENDING),
                ("metadata.date_epoch", DESCENDING)
            ])
            
            # Index on sender for search
            self.emails_collection.create_index([("sender", ASCENDING)])
            
            # Index on filtered field
            self.emails_collection.create_index([("filtered", ASCENDING)])
            
            # Text search index
            self.emails_collection.create_index([
                ("email_subject", "text"),
                ("email_body", "text"),
                ("sender", "text")
            ])
            
            # Response collection indexes
            if self.responses_collection:
                self.responses_collection.create_index([("email_id", ASCENDING)])
                self.responses_collection.create_index([("status", ASCENDING)])
                self.responses_collection.create_index([("created_at", DESCENDING)])
            
            logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def insert_email(self, email_record: EmailRecord) -> Optional[str]:
        """Insert email record into MongoDB"""
        if self.emails_collection:
            try:
                result = self.emails_collection.insert_one(email_record.to_dict())
                logger.debug(f"Inserted email with ID: {result.inserted_id}")
                return str(result.inserted_id)
            except Exception as e:
                logger.error(f"Error inserting email: {e}")
                return None
        else:
            # Use in-memory storage
            email_dict = email_record.to_dict()
            self._memory_storage.append(email_dict)
            logger.debug(f"Inserted email with ID: {email_dict['_id']}")
            return email_dict['_id']
    
    def update_email_embeddings(self, email_id: str, embeddings: Dict[str, Any]) -> bool:
        """Update email record with embedding information"""
        if self.emails_collection:
            try:
                result = self.emails_collection.update_one(
                    {"_id": email_id},
                    {
                        "$set": {
                            "embeddings": embeddings,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                )
                return result.modified_count > 0
            except Exception as e:
                logger.error(f"Error updating embeddings: {e}")
                return False
        else:
            # Use in-memory storage
            try:
                for email in self._memory_storage:
                    if email["_id"] == email_id or str(email["_id"]) == str(email_id):
                        email["embeddings"] = embeddings
                        email["updated_at"] = datetime.utcnow().isoformat()
                        return True
                return False
            except Exception as e:
                logger.error(f"Error updating embeddings in memory: {e}")
                return False
    
    def get_emails(self, 
                   page: int = 1, 
                   page_size: int = 20,
                   filters: Optional[Dict[str, Any]] = None,
                   sort: Optional[List[Tuple[str, int]]] = None) -> Dict[str, Any]:
        """Get emails with pagination and filtering"""
        filters = filters or {}
        sort = sort or [("metadata.date_epoch", DESCENDING)]
        
        if self.emails_collection:
            try:
                # Calculate skip
                skip = (page - 1) * page_size
                
                # Execute query
                cursor = self.emails_collection.find(filters).sort(sort).skip(skip).limit(page_size)
                emails = list(cursor)
                
                # Get total count
                total = self.emails_collection.count_documents(filters)
                
                # Convert ObjectId to string for JSON serialization
                for email in emails:
                    if isinstance(email.get("_id"), ObjectId):
                        email["_id"] = str(email["_id"])
                
                return {
                    "data": emails,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size
                }
                
            except Exception as e:
                logger.error(f"Error getting emails: {e}")
                return {"data": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
        else:
            # Use in-memory storage
            try:
                # Simple in-memory filtering and sorting
                filtered_emails = self._memory_storage.copy()
                
                # Apply filters (simplified)
                if filters:
                    filtered_emails = [email for email in filtered_emails if self._matches_filters(email, filters)]
                
                # Sort (simplified)
                if sort:
                    sort_field, sort_order = sort[0]
                    reverse = sort_order == DESCENDING
                    filtered_emails.sort(key=lambda x: x.get(sort_field, 0), reverse=reverse)
                
                total = len(filtered_emails)
                
                # Paginate
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                emails = filtered_emails[start_idx:end_idx]
                
                # Convert ObjectId to string
                for email in emails:
                    if hasattr(email["_id"], "__str__"):
                        email["_id"] = str(email["_id"])
                
                return {
                    "data": emails,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size
                }
            except Exception as e:
                logger.error(f"Error getting emails from memory: {e}")
                return {"data": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
    
    def get_email_by_id(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Get single email by ID"""
        if self.emails_collection:
            try:
                email = self.emails_collection.find_one({"_id": email_id})
                if email and isinstance(email.get("_id"), ObjectId):
                    email["_id"] = str(email["_id"])
                return email
            except Exception as e:
                logger.error(f"Error getting email by ID: {e}")
                return None
        else:
            # Use in-memory storage
            try:
                for email in self._memory_storage:
                    if str(email["_id"]) == email_id:
                        email_copy = email.copy()
                        email_copy["_id"] = str(email_copy["_id"])
                        return email_copy
                return None
            except Exception as e:
                logger.error(f"Error getting email by ID from memory: {e}")
                return None
    
    def get_emails_by_ids(self, email_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple emails by IDs"""
        if self.emails_collection:
            try:
                cursor = self.emails_collection.find({"_id": {"$in": email_ids}})
                emails = list(cursor)
                
                # Convert ObjectId to string
                for email in emails:
                    if isinstance(email.get("_id"), ObjectId):
                        email["_id"] = str(email["_id"])
                
                return emails
            except Exception as e:
                logger.error(f"Error getting emails by IDs: {e}")
                return []
        else:
            # Use in-memory storage
            try:
                results = []
                for email in self._memory_storage:
                    if str(email["_id"]) in email_ids:
                        email_copy = email.copy()
                        email_copy["_id"] = str(email_copy["_id"])
                        results.append(email_copy)
                return results
            except Exception as e:
                logger.error(f"Error getting emails by IDs from memory: {e}")
                return []
    
    def vector_search(self, query_vector: List[float], k: int = 25, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Perform vector search using MongoDB Atlas Vector Search"""
        if not self.emails_collection:
            logger.warning("MongoDB collection not available")
            return []
        
        try:
            # MongoDB Atlas Vector Search pipeline
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "path": "embeddings.vector",
                        "queryVector": query_vector,
                        "numCandidates": k * 10,
                        "limit": k
                    }
                }
            ]
            
            # Add filters if provided
            if filters:
                pipeline.append({"$match": filters})
            
            # Add vector search score
            pipeline.append({
                "$addFields": {
                    "score": {"$meta": "vectorSearchScore"}
                }
            })
            
            results = list(self.emails_collection.aggregate(pipeline))
            
            # Convert ObjectId to string
            for result in results:
                if isinstance(result.get("_id"), ObjectId):
                    result["_id"] = str(result["_id"])
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing vector search: {e}")
            # Fallback to text search
            return self._fallback_text_search(filters or {}, k)
    
    def _fallback_text_search(self, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Fallback text search when vector search fails"""
        try:
            cursor = self.emails_collection.find(filters).limit(limit)
            results = list(cursor)
            
            # Add dummy score
            for result in results:
                result["score"] = 0.5
                if isinstance(result.get("_id"), ObjectId):
                    result["_id"] = str(result["_id"])
            
            return results
        except Exception as e:
            logger.error(f"Error in fallback text search: {e}")
            return []
    
    def _matches_filters(self, email: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if email matches filters (for in-memory storage)"""
        try:
            for field, value in filters.items():
                if field in email and email[field] != value:
                    return False
            return True
        except Exception:
            return False
    
    # Draft Response Methods
    def insert_draft_response(self, draft_response: DraftResponse) -> Optional[str]:
        """Insert draft response"""
        if self.responses_collection:
            try:
                result = self.responses_collection.insert_one(draft_response.to_dict())
                return str(result.inserted_id)
            except Exception as e:
                logger.error(f"Error inserting draft response: {e}")
                return None
        else:
            # Use in-memory storage
            response_dict = draft_response.to_dict()
            self._memory_responses.append(response_dict)
            return response_dict['_id']
    
    def get_draft_responses(self, status: Optional[str] = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get draft responses with pagination"""
        filters = {}
        if status:
            filters["status"] = status
        
        if self.responses_collection:
            try:
                skip = (page - 1) * page_size
                cursor = self.responses_collection.find(filters).sort([("created_at", DESCENDING)]).skip(skip).limit(page_size)
                responses = list(cursor)
                total = self.responses_collection.count_documents(filters)
                
                for response in responses:
                    if isinstance(response.get("_id"), ObjectId):
                        response["_id"] = str(response["_id"])
                
                return {
                    "data": responses,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size
                }
            except Exception as e:
                logger.error(f"Error getting draft responses: {e}")
                return {"data": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
        else:
            # Use in-memory storage
            filtered_responses = [r for r in self._memory_responses if not status or r.get("status") == status]
            total = len(filtered_responses)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            responses = filtered_responses[start_idx:end_idx]
            
            return {
                "data": responses,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
    
    def update_draft_response_status(self, response_id: str, status: str, approved_by: str = None) -> bool:
        """Update draft response status"""
        updates = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if approved_by:
            updates["approved_by"] = approved_by
            updates["approved_at"] = datetime.utcnow().isoformat()
        
        if status == "sent":
            updates["sent_at"] = datetime.utcnow().isoformat()
        
        if self.responses_collection:
            try:
                result = self.responses_collection.update_one(
                    {"_id": response_id},
                    {"$set": updates}
                )
                return result.modified_count > 0
            except Exception as e:
                logger.error(f"Error updating draft response: {e}")
                return False
        else:
            # Use in-memory storage
            for response in self._memory_responses:
                if response["_id"] == response_id:
                    response.update(updates)
                    return True
            return False

# Global service instance
mongodb_service = MongoDBService()
