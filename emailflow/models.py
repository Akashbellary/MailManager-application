


from datetime import datetime
from typing import Dict, List, Optional
import json
from bson import ObjectId

class Email:
    """Email model for MongoDB documents"""
    
    def __init__(self, data: Dict):
        self._id = data.get('_id')
        # Generate ObjectId if _id is not provided
        if self._id is None:
            self._id = ObjectId()
        self.sender = data.get('sender', '')
        self.email_subject = data.get('email_subject', '')
        self.email_body = data.get('email_body', '')
        self.priority = data.get('priority', 'Low Priority')
        self.sentiment = data.get('sentiment', 'Neutral')
        self.classification = data.get('classification', 'General')
        self.summary = data.get('summary', '')
        self.filtered = data.get('filtered', False)
        self.metadata = data.get('metadata', {})
        self.other_details = data.get('other_details', {})
        self.suggested_responses = data.get('suggested_responses', [])
        self.embeddings = data.get('embeddings', {})
        self.created_at = data.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = data.get('updated_at', datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            '_id': self._id,
            'sender': self.sender,
            'email_subject': self.email_subject,
            'email_body': self.email_body,
            'priority': self.priority,
            'sentiment': self.sentiment,
            'classification': self.classification,
            'summary': self.summary,
            'filtered': self.filtered,
            'metadata': self.metadata,
            'other_details': self.other_details,
            'suggested_responses': self.suggested_responses,
            'embeddings': self.embeddings,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class Response:
    """Response model for MongoDB documents"""
    
    def __init__(self, data: Dict):
        self._id = data.get('_id')
        # Generate ObjectId if _id is not provided
        if self._id is None:
            self._id = ObjectId()
        self.email_id = data.get('email_id')
        self.response_text = data.get('response_text', '')
        self.status = data.get('status', 'pending')  # pending, approved, sent, rejected
        self.created_at = data.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = data.get('updated_at', datetime.utcnow().isoformat())
        self.approved_by = data.get('approved_by')
        self.sent_at = data.get('sent_at')
        self.recipient = data.get('recipient', '')
        self.subject = data.get('subject', '')
    
    def to_dict(self) -> Dict:
        return {
            '_id': self._id,
            'email_id': self.email_id,
            'response_text': self.response_text,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'approved_by': self.approved_by,
            'sent_at': self.sent_at,
            'recipient': self.recipient,
            'subject': self.subject
        }

class UploadProgress:
    """Upload progress tracking model"""
    
    def __init__(self, data: Dict):
        self._id = data.get('_id')
        # FIX: Generate ObjectId if _id is not provided
        if self._id is None:
            self._id = ObjectId()
        self.filename = data.get('filename', '')
        self.total_rows = data.get('total_rows', 0)
        self.processed_rows = data.get('processed_rows', 0)
        self.error_count = data.get('error_count', 0)  # Track processing errors
        self.status = data.get('status', 'processing')  # processing, completed, failed
        self.error_message = data.get('error_message', '')
        self.created_at = data.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = data.get('updated_at', datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            '_id': self._id,
            'filename': self.filename,
            'total_rows': self.total_rows,
            'processed_rows': self.processed_rows,
            'error_count': self.error_count,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @property
    def progress_percentage(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return (self.processed_rows / self.total_rows) * 100