import os
import logging
import json
from typing import Dict, List, Optional, Any
from openai import OpenAI
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = None
        self.initialize_client()
        # Initialize local embedding model (100% working, no API key needed)
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')  # Fast and effective model
    
    def initialize_client(self):
        """Initialize OpenAI client with NVIDIA API for chat completions"""
        try:
            api_key = os.getenv('NVIDIA_API_KEY', 'nvapi-default-key')
            base_url = os.getenv('NVIDIA_BASE_URL', 'https://integrate.api.nvidia.com/v1')
            
            # Only pass valid arguments to OpenAI constructor
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            logger.info("AI Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI Service: {e}")
            self.client = None
    
    def generate_embeddings(self, texts):
        """Generate embeddings for texts using local sentence-transformers"""
        try:
            # Use local embedder instead of API
            embeddings = self.embedder.encode(texts)
            return embeddings.tolist()  # Return as list of lists for consistency
        
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
        
    def classify_email(self, subject: str, body: str) -> Dict[str, str]:
        """Classify email priority, sentiment, and category"""
        if not self.client:
            logger.error("AI client not initialized - cannot classify email")
            raise Exception("AI service not properly initialized. Cannot classify email.")
        
        try:
            prompt = f"""
            Analyze the following email and provide classification:
            
            Subject: {subject}
            Body: {body}
            
            Please respond with a JSON object containing:
            1. priority: \"High Priority\", \"Medium Priority\", or \"Low Priority\"
            2. sentiment: \"Positive\", \"Neutral\", or \"Negative\"
            3. classification: one of \"Support\", \"Query\", \"Request\", \"Help\"
            4. summary: a brief 1-2 sentence summary of the email
            
            Consider:
            - High Priority: urgent issues, problems, complaints, technical issues
            - Medium Priority: requests, questions, inquiries
            - Low Priority: general information, thank you messages
            
            Response format (JSON only):
            """
            
            response = self.client.chat.completions.create(
                model="nvidia/nvidia-nemotron-nano-9b-v2",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
                extra_body={
                    "min_thinking_tokens": 128,
                    "max_thinking_tokens": 256
                }
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
            
            raise Exception("Invalid response from AI service")
            
        except Exception as e:
            logger.error(f"Error classifying email: {e}")
            raise Exception(f"Failed to classify email: {str(e)}")
    
    def generate_response(self, subject: str, body: str, classification: str) -> Optional[str]:
        """Generate suggested response based on classification"""
        if not self.client:
            logger.error("AI client not initialized - cannot generate response")
            raise Exception("AI service not properly initialized. Cannot generate response.")
        
        try:
            prompt = f"""
            Generate a professional email response for the following:
            
            Classification: {classification}
            Subject: {subject}
            Body: {body}
            
            Response should be polite, concise, and address the main points.
            """
            
            response = self.client.chat.completions.create(
                model="nvidia/nvidia-nemotron-nano-9b-v2",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=500,
                extra_body={
                    "min_thinking_tokens": 128,
                    "max_thinking_tokens": 256
                }
            )
            
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            
            raise Exception("Invalid response from AI service")
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    def interpret_search_query(self, query: str) -> Dict[str, Any]:
        """Interpret natural language search query"""
        if not self.client:
            logger.error("AI client not initialized - cannot interpret search query")
            raise Exception("AI service not properly initialized. Cannot interpret search query.")
        
        try:
            prompt = f"""
            Interpret the following natural language search query for email search:
            
            Query: \"{query}\"
            
            Extract the following information and respond with JSON:
            1. filters: object with keys priority, sentiment, classification (values should be arrays)
            2. search_terms: array of keywords to search in email content
            3. sender_filters: array of sender-related terms
            4. intent: brief description of what user is looking for
            
            Available values:
            - priority: [\"High Priority\", \"Medium Priority\", \"Low Priority\"]
            - sentiment: [\"Positive\", \"Neutral\", \"Negative\"]
            - classification: [\"Support\", \"Query\", \"Request\", \"Help\", \"Complaint\", \"General\"]
            
            Examples:
            \"negative emails\" -> {{\"filters\": {{\"sentiment\": [\"Negative\"]}}, \"search_terms\": [], \"sender_filters\": [], \"intent\": \"emails with negative sentiment\"}}
            \"emails from alice\" -> {{\"filters\": {{}}, \"search_terms\": [], \"sender_filters\": [\"alice\"], \"intent\": \"emails from alice\"}}
            \"high priority support tickets\" -> {{\"filters\": {{\"priority\": [\"High Priority\"], \"classification\": [\"Support\"]}}, \"search_terms\": [\"tickets\"], \"sender_filters\": [], \"intent\": \"high priority support emails\"}}
            
            Response (JSON only):
            """
            
            response = self.client.chat.completions.create(
                model="nvidia/nvidia-nemotron-nano-9b-v2",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300,
                extra_body={
                    "min_thinking_tokens": 128,
                    "max_thinking_tokens": 256
                }
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
            
            raise Exception("Invalid response from AI service")
            
        except Exception as e:
            logger.error(f"Error interpreting search query: {e}")
            raise Exception(f"Failed to interpret search query: {str(e)}")

# Global AI service instance
ai_service = AIService()