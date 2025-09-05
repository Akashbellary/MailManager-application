from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

class EmailRecord:
    """Email record model for MongoDB storage"""
    
    def __init__(self, 
                 sender: str,
                 email_subject: str,
                 email_body: str,
                 filtered: bool = False,
                 priority: str = "Medium Priority",
                 classification: str = "Query",
                 sentiment: str = "Neutral",
                 suggested_responses: List[str] = None,
                 other_details: Dict[str, Any] = None,
                 summary: str = "",
                 metadata: Dict[str, Any] = None,
                 embeddings: Dict[str, Any] = None,
                 _id: str = None):
        
        self.sender = sender
        self.email_subject = email_subject
        self.email_body = email_body
        self.filtered = filtered
        self.priority = priority
        self.classification = classification
        self.sentiment = sentiment
        self.suggested_responses = suggested_responses or []
        self.other_details = other_details or {}
        self.summary = summary
        self.metadata = metadata or {}
        self.embeddings = embeddings or {}
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        self._id = _id or str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return {
            "_id": self._id,
            "sender": self.sender,
            "email_subject": self.email_subject,
            "email_body": self.email_body,
            "filtered": self.filtered,
            "priority": self.priority,
            "classification": self.classification,
            "sentiment": self.sentiment,
            "suggested_responses": self.suggested_responses,
            "other_details": self.other_details,
            "summary": self.summary,
            "metadata": self.metadata,
            "embeddings": self.embeddings,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailRecord':
        """Create EmailRecord from dictionary"""
        return cls(
            sender=data.get("sender", ""),
            email_subject=data.get("email_subject", ""),
            email_body=data.get("email_body", ""),
            filtered=data.get("filtered", False),
            priority=data.get("priority", "Medium Priority"),
            classification=data.get("classification", "Query"),
            sentiment=data.get("sentiment", "Neutral"),
            suggested_responses=data.get("suggested_responses", []),
            other_details=data.get("other_details", {}),
            summary=data.get("summary", ""),
            metadata=data.get("metadata", {}),
            embeddings=data.get("embeddings", {}),
            _id=data.get("_id")
        )

class DraftResponse:
    """Draft response model for approval workflow"""
    
    def __init__(self,
                 email_id: str,
                 response_text: str,
                 created_by: str = "system",
                 status: str = "pending",
                 priority: str = "medium",
                 _id: str = None):
        
        self.email_id = email_id
        self.response_text = response_text
        self.created_by = created_by
        self.status = status  # pending, approved, rejected, sent
        self.priority = priority
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        self.approved_by = None
        self.approved_at = None
        self.sent_at = None
        self._id = _id or str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return {
            "_id": self._id,
            "email_id": self.email_id,
            "response_text": self.response_text,
            "created_by": self.created_by,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "sent_at": self.sent_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DraftResponse':
        """Create DraftResponse from dictionary"""
        draft = cls(
            email_id=data.get("email_id", ""),
            response_text=data.get("response_text", ""),
            created_by=data.get("created_by", "system"),
            status=data.get("status", "pending"),
            priority=data.get("priority", "medium"),
            _id=data.get("_id")
        )
        draft.approved_by = data.get("approved_by")
        draft.approved_at = data.get("approved_at")
        draft.sent_at = data.get("sent_at")
        return draft

class SearchResult:
    """Search result model"""
    
    def __init__(self, email_record: Dict[str, Any], score: float, highlights: List[str] = None):
        self.email_record = email_record
        self.score = score
        self.highlights = highlights or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "email_record": self.email_record,
            "score": self.score,
            "highlights": self.highlights
        }
