import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.nvidia_client import nvidia_client
from services.mongodb_service import mongodb_service
from models import DraftResponse

logger = logging.getLogger(__name__)

class ApprovalService:
    """Service for managing email response approval workflow"""
    
    def __init__(self):
        pass
    
    def generate_draft_response(self, email_id: str, use_suggested: bool = False) -> Optional[str]:
        """Generate draft response for an email"""
        try:
            # Get email details
            email = mongodb_service.get_email_by_id(email_id)
            if not email:
                logger.error(f"Email not found: {email_id}")
                return None
            
            if use_suggested and email.get("suggested_responses"):
                # Use one of the suggested responses
                suggested = email["suggested_responses"][0] if email["suggested_responses"] else ""
                if suggested:
                    # Expand the suggested response
                    draft_text = f"Dear {email.get('sender', 'Customer')},\n\n{suggested}\n\nBest regards,\nCustomer Support Team"
                else:
                    draft_text = self._generate_ai_response(email)
            else:
                # Generate new response using AI
                draft_text = self._generate_ai_response(email)
            
            # Create draft response record
            draft_response = DraftResponse(
                email_id=email_id,
                response_text=draft_text,
                created_by="system",
                status="pending",
                priority=self._determine_response_priority(email.get("priority", "Medium Priority"))
            )
            
            # Save to database
            draft_id = mongodb_service.insert_draft_response(draft_response)
            if draft_id:
                logger.info(f"Created draft response {draft_id} for email {email_id}")
                return draft_id
            else:
                logger.error("Failed to save draft response")
                return None
                
        except Exception as e:
            logger.error(f"Error generating draft response: {e}")
            return None
    
    def _generate_ai_response(self, email: Dict[str, Any]) -> str:
        """Generate AI response for email"""
        try:
            response = nvidia_client.generate_response(
                email_subject=email.get("email_subject", ""),
                email_body=email.get("email_body", ""),
                sender=email.get("sender", "")
            )
            return response or "Thank you for your email. We have received your message and will respond shortly."
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "Thank you for your email. We have received your message and will respond shortly."
    
    def _determine_response_priority(self, email_priority: str) -> str:
        """Determine response priority based on email priority"""
        priority_mapping = {
            "High Priority": "high",
            "Medium Priority": "medium", 
            "Low Priority": "low"
        }
        return priority_mapping.get(email_priority, "medium")
    
    def get_pending_responses(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get pending responses for approval"""
        try:
            result = mongodb_service.get_draft_responses(
                status="pending",
                page=page,
                page_size=page_size
            )
            
            # Enrich with email details
            for response in result["data"]:
                email = mongodb_service.get_email_by_id(response["email_id"])
                if email:
                    response["email_details"] = {
                        "subject": email.get("email_subject", ""),
                        "sender": email.get("sender", ""),
                        "priority": email.get("priority", ""),
                        "classification": email.get("classification", ""),
                        "sentiment": email.get("sentiment", "")
                    }
                else:
                    response["email_details"] = {}
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting pending responses: {e}")
            return {"data": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
    
    def approve_response(self, response_id: str, approved_by: str = "admin") -> bool:
        """Approve a draft response"""
        try:
            success = mongodb_service.update_draft_response_status(
                response_id=response_id,
                status="approved",
                approved_by=approved_by
            )
            
            if success:
                logger.info(f"Response {response_id} approved by {approved_by}")
                # Keep response as approved, don't automatically mark as sent
                return True
            
            return success
            
        except Exception as e:
            logger.error(f"Error approving response: {e}")
            return False
    
    def reject_response(self, response_id: str, rejected_by: str = "admin") -> bool:
        """Reject a draft response"""
        try:
            success = mongodb_service.update_draft_response_status(
                response_id=response_id,
                status="rejected",
                approved_by=rejected_by
            )
            
            if success:
                logger.info(f"Response {response_id} rejected by {rejected_by}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error rejecting response: {e}")
            return False
    
    def mark_as_sent(self, response_id: str) -> bool:
        """Mark response as sent"""
        try:
            success = mongodb_service.update_draft_response_status(
                response_id=response_id,
                status="sent"
            )
            
            if success:
                logger.info(f"Response {response_id} marked as sent")
            
            return success
            
        except Exception as e:
            logger.error(f"Error marking response as sent: {e}")
            return False
    
    def get_response_statistics(self) -> Dict[str, Any]:
        """Get response statistics for dashboard"""
        try:
            # Get counts for different statuses
            pending_result = mongodb_service.get_draft_responses(status="pending", page_size=1)
            approved_result = mongodb_service.get_draft_responses(status="approved", page_size=1)
            sent_result = mongodb_service.get_draft_responses(status="sent", page_size=1)
            rejected_result = mongodb_service.get_draft_responses(status="rejected", page_size=1)
            
            return {
                "pending": pending_result["total"],
                "approved": approved_result["total"],
                "sent": sent_result["total"],
                "rejected": rejected_result["total"],
                "total": (pending_result["total"] + approved_result["total"] + 
                         sent_result["total"] + rejected_result["total"])
            }
            
        except Exception as e:
            logger.error(f"Error getting response statistics: {e}")
            return {
                "pending": 0,
                "approved": 0,
                "sent": 0,
                "rejected": 0,
                "total": 0
            }

# Global service instance
approval_service = ApprovalService()
