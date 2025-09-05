import os
import logging
import json
from typing import Dict, List, Optional, Any
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = None
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize OpenAI client with NVIDIA API"""
        try:
            api_key = os.getenv('NVIDIA_API_KEY', 'nvapi-default-key')
            base_url = os.getenv('NVIDIA_BASE_URL', 'https://integrate.api.nvidia.com/v1')
            
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            logger.info("AI Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI Service: {e}")
            self.client = None
    
    def generate_embeddings(self, text: str) -> Optional[List[float]]:
        """Generate embeddings for text"""
        if not self.client:
            logger.warning("AI client not initialized")
            return None
        
        try:
            response = self.client.embeddings.create(
                input=[text],
                model="nvidia/nv-embedqa-e5-v5",
                encoding_format="float"
            )
            
            if response.data:
                return response.data[0].embedding
            return None
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None
    
    def classify_email(self, subject: str, body: str) -> Dict[str, str]:
        """Classify email priority, sentiment, and category"""
        if not self.client:
            logger.warning("AI client not initialized - using fallback classification")
            return self._fallback_classification(subject, body)
        
        try:
            prompt = f"""
            Analyze the following email and provide classification:
            
            Subject: {subject}
            Body: {body}
            
            Please respond with a JSON object containing:
            1. priority: "High Priority", "Medium Priority", or "Low Priority"
            2. sentiment: "Positive", "Neutral", or "Negative"
            3. classification: one of "Support", "Query", "Request", "Help", "Complaint", "General"
            4. summary: a brief 1-2 sentence summary of the email
            
            Consider:
            - High Priority: urgent issues, problems, complaints, technical issues
            - Medium Priority: requests, questions, inquiries
            - Low Priority: general information, thank you messages
            
            Response format (JSON only):
            """
            
            response = self.client.chat.completions.create(
                model="meta/llama-3.1-405b-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            if response.choices and response.choices[0].message.content:
                content = response.choices[0].message.content.strip()
                # Extract JSON from response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    result = json.loads(json_content)
                    
                    # Validate and normalize response
                    return {
                        'priority': result.get('priority', 'Medium Priority'),
                        'sentiment': result.get('sentiment', 'Neutral'),
                        'classification': result.get('classification', 'General'),
                        'summary': result.get('summary', '')
                    }
            
            return self._fallback_classification(subject, body)
            
        except Exception as e:
            logger.error(f"Error classifying email: {e}")
            return self._fallback_classification(subject, body)
    
    def _fallback_classification(self, subject: str, body: str) -> Dict[str, str]:
        """Fallback classification when AI is not available"""
        text = (subject + " " + body).lower()
        
        # Simple keyword-based classification
        priority = "Low Priority"
        sentiment = "Neutral"
        classification = "General"
        
        # Priority keywords
        high_priority_keywords = ['urgent', 'emergency', 'asap', 'critical', 'problem', 'error', 'issue', 'broken', 'failed', 'help']
        medium_priority_keywords = ['question', 'inquiry', 'request', 'need', 'want', 'how', 'when', 'where']
        
        if any(keyword in text for keyword in high_priority_keywords):
            priority = "High Priority"
        elif any(keyword in text for keyword in medium_priority_keywords):
            priority = "Medium Priority"
        
        # Sentiment keywords
        positive_keywords = ['thank', 'great', 'excellent', 'good', 'happy', 'satisfied', 'love']
        negative_keywords = ['problem', 'issue', 'error', 'failed', 'broken', 'angry', 'frustrated', 'terrible']
        
        if any(keyword in text for keyword in positive_keywords):
            sentiment = "Positive"
        elif any(keyword in text for keyword in negative_keywords):
            sentiment = "Negative"
        
        # Classification keywords
        if any(keyword in text for keyword in ['support', 'help', 'assist']):
            classification = "Support"
        elif any(keyword in text for keyword in ['question', 'how', 'what', 'why']):
            classification = "Query"
        elif any(keyword in text for keyword in ['request', 'need', 'want']):
            classification = "Request"
        elif any(keyword in text for keyword in ['problem', 'issue', 'error']):
            classification = "Help"
        
        return {
            'priority': priority,
            'sentiment': sentiment,
            'classification': classification,
            'summary': f"Email from sender regarding {classification.lower()}"
        }
    
    def generate_response(self, email_subject: str, email_body: str, email_classification: str) -> Optional[str]:
        """Generate AI response for email"""
        if not self.client:
            logger.warning("AI client not initialized - using fallback response")
            return self._fallback_response(email_classification)
        
        try:
            prompt = f"""
            Generate a professional email response for the following customer email:
            
            Subject: {email_subject}
            Body: {email_body}
            Classification: {email_classification}
            
            Please generate a helpful, professional, and empathetic response that:
            1. Acknowledges the customer's concern/question
            2. Provides helpful information or next steps
            3. Maintains a professional tone
            4. Is concise but complete
            
            Response:
            """
            
            response = self.client.chat.completions.create(
                model="meta/llama-3.1-405b-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            if response.choices:
                return response.choices[0].message.content.strip()
            
            return self._fallback_response(email_classification)
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._fallback_response(email_classification)
    
    def _fallback_response(self, classification: str) -> str:
        """Fallback response templates"""
        templates = {
            'Support': "Thank you for contacting our support team. We have received your request and will respond within 24 hours. If this is urgent, please call our support line.",
            'Query': "Thank you for your inquiry. We will review your question and provide a detailed response shortly. Please allow 1-2 business days for our response.",
            'Request': "We have received your request and will process it as soon as possible. You will receive an update within 2-3 business days.",
            'Help': "We understand you're experiencing an issue and we're here to help. Our technical team will investigate and respond with a solution within 24 hours.",
            'Complaint': "We apologize for any inconvenience you've experienced. Your feedback is important to us and we will address your concerns promptly.",
            'General': "Thank you for your email. We have received your message and will respond appropriately."
        }
        return templates.get(classification, templates['General'])
    
    def interpret_search_query(self, query: str) -> Dict[str, Any]:
        """Interpret natural language search query"""
        if not self.client:
            logger.warning("AI client not initialized - using fallback query interpretation")
            return self._fallback_query_interpretation(query)
        
        try:
            prompt = f"""
            Interpret the following natural language search query for email search:
            
            Query: "{query}"
            
            Extract the following information and respond with JSON:
            1. filters: object with keys priority, sentiment, classification (values should be arrays)
            2. search_terms: array of keywords to search in email content
            3. sender_filters: array of sender-related terms
            4. intent: brief description of what user is looking for
            
            Available values:
            - priority: ["High Priority", "Medium Priority", "Low Priority"]
            - sentiment: ["Positive", "Neutral", "Negative"]
            - classification: ["Support", "Query", "Request", "Help", "Complaint", "General"]
            
            Examples:
            "negative emails" -> {{"filters": {{"sentiment": ["Negative"]}}, "search_terms": [], "sender_filters": [], "intent": "emails with negative sentiment"}}
            "emails from alice" -> {{"filters": {{}}, "search_terms": [], "sender_filters": ["alice"], "intent": "emails from alice"}}
            "high priority support tickets" -> {{"filters": {{"priority": ["High Priority"], "classification": ["Support"]}}, "search_terms": ["tickets"], "sender_filters": [], "intent": "high priority support emails"}}
            
            Response (JSON only):
            """
            
            response = self.client.chat.completions.create(
                model="meta/llama-3.1-405b-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            if response.choices and response.choices[0].message.content:
                content = response.choices[0].message.content.strip()
                # Extract JSON from response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    result = json.loads(json_content)
                    return result
            
            return self._fallback_query_interpretation(query)
            
        except Exception as e:
            logger.error(f"Error interpreting search query: {e}")
            return self._fallback_query_interpretation(query)
    
    def _fallback_query_interpretation(self, query: str) -> Dict[str, Any]:
        """Fallback query interpretation"""
        query_lower = query.lower()
        
        filters = {}
        search_terms = []
        sender_filters = []
        
        # Priority keywords
        if any(word in query_lower for word in ['high priority', 'urgent', 'critical']):
            filters['priority'] = ['High Priority']
        elif any(word in query_lower for word in ['medium priority', 'normal']):
            filters['priority'] = ['Medium Priority']
        elif any(word in query_lower for word in ['low priority']):
            filters['priority'] = ['Low Priority']
        
        # Sentiment keywords
        if any(word in query_lower for word in ['negative', 'bad', 'angry', 'frustrated']):
            filters['sentiment'] = ['Negative']
        elif any(word in query_lower for word in ['positive', 'good', 'happy', 'satisfied']):
            filters['sentiment'] = ['Positive']
        elif any(word in query_lower for word in ['neutral']):
            filters['sentiment'] = ['Neutral']
        
        # Classification keywords
        if any(word in query_lower for word in ['support', 'help']):
            filters['classification'] = ['Support']
        elif any(word in query_lower for word in ['question', 'query']):
            filters['classification'] = ['Query']
        elif any(word in query_lower for word in ['request']):
            filters['classification'] = ['Request']
        elif any(word in query_lower for word in ['complaint']):
            filters['classification'] = ['Complaint']
        
        # Sender filters
        if 'from' in query_lower or 'by' in query_lower:
            # Extract potential sender names
            words = query.split()
            for i, word in enumerate(words):
                if word.lower() in ['from', 'by'] and i + 1 < len(words):
                    sender_filters.append(words[i + 1])
        
        # Search terms (remaining words)
        excluded_words = ['emails', 'email', 'list', 'all', 'with', 'from', 'by', 'high', 'medium', 'low', 'priority', 'positive', 'negative', 'neutral']
        search_terms = [word for word in query.split() if word.lower() not in excluded_words and word not in sender_filters]
        
        return {
            'filters': filters,
            'search_terms': search_terms,
            'sender_filters': sender_filters,
            'intent': f"Search for: {query}"
        }

# Global AI service instance
ai_service = AIService()
