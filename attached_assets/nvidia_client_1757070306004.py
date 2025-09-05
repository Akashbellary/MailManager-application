import os
import logging
from typing import List, Dict, Any, Optional
import json
import time

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    # Create a dummy OpenAI class
    class OpenAI:
        def __init__(self, *args, **kwargs):
            pass
        
        @property
        def chat(self):
            return self
        
        @property
        def completions(self):
            return self
        
        @property
        def embeddings(self):
            return self
        
        def create(self, *args, **kwargs):
            raise Exception("OpenAI client not available")

logger = logging.getLogger(__name__)

class NVIDIAClient:
    """NVIDIA API client for LLM and embeddings"""
    
    def __init__(self):
        self.api_key = os.getenv("NVIDIA_API_KEY", "")
        self.base_url = "https://integrate.api.nvidia.com/v1"
        
        if not self.api_key:
            logger.warning("NVIDIA_API_KEY not found in environment variables")
        
        if OPENAI_AVAILABLE:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
        else:
            logger.warning("OpenAI client not available")
            self.client = None
        
        # Model preferences in order
        self.llm_models = [
            "openai/gpt-oss-20b",
            "meta/llama-3.1-70b-instruct",
            "openai/gpt-4o-mini"
        ]
        
        self.embedding_model = "nvidia/nv-embed-v1"
    
    def classify_email(self, subject: str, body: str, sender: str = "") -> Optional[Dict[str, Any]]:
        """Classify email using NVIDIA LLM"""
        
        system_prompt = """You are a precise email triage assistant. Given subject, body, and optional sender, produce a strict JSON object with keys:

filtered (boolean): true if spam/irrelevant/autoresponder; else false.

priority (one of: "High Priority", "Medium Priority", "Low Priority"). Consider urgency, deadlines, account issues, downtime, escalation keywords.

classification (one of: "Support", "Query", "Request", "Help").

sentiment (one of: "Positive", "Neutral", "Negative").

suggested_responses (exactly 3 brief, email-ready sentences tailored to the message; do not include greetings/signatures).

other_details:
phone_number (string|null; India or international formats) – prefer regex extraction; if none, null.
address (string|null; concise, single line).
alternate_email (string|null; any email addresses inside the body besides sender).

summary (1–2 sentences capturing intent and required action).

metadata:
date (ISO-8601 string): Do not infer; a separate process fills this from CSV. Return the placeholder value "$CSV_DATE_WILL_BE_FILLED_SEPARATELY".

Rules:
- Do not re-infer CSV fields (sender, subject, body, date).
- Only use the provided subject and body to infer the target fields.
- Output valid JSON only; no comments, no markdown.
- Keys must exactly match and include all required fields.
- suggested_responses must be short, factual, and non-committal unless the email explicitly requests a commitment."""

        user_prompt = f"""Subject: {subject}
Body: {body}
Sender: {sender}

Analyze this email and return the classification JSON."""

        for model in self.llm_models:
            try:
                logger.debug(f"Trying model: {model}")
                
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2048
                )
                
                response_text = completion.choices[0].message.content.strip()
                logger.debug(f"Raw LLM response: {response_text}")
                
                # Try to parse JSON
                try:
                    result = json.loads(response_text)
                    logger.debug(f"Successfully parsed JSON from {model}")
                    return result
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error from {model}: {e}")
                    # Try to repair JSON
                    repaired = self._repair_json(response_text)
                    if repaired:
                        return repaired
                    continue
                    
            except Exception as e:
                logger.error(f"Error with model {model}: {e}")
                continue
        
        logger.error("All LLM models failed, returning fallback")
        return self._get_fallback_classification()
    
    def generate_response(self, email_subject: str, email_body: str, sender: str = "") -> Optional[str]:
        """Generate email response using NVIDIA LLM"""
        
        if not self.client:
            logger.error("NVIDIA client not available")
            return "Thank you for your email. We have received your message and will respond shortly."
        
        system_prompt = """You are a professional email response assistant. Generate a complete, polite, and helpful email response.

Guidelines:
- Be professional and courteous
- Address the sender's concerns directly
- Provide helpful information or next steps
- Keep the response concise but complete
- Include appropriate greetings and closing
- Do not make commitments you cannot keep
- If you cannot resolve the issue, acknowledge it and provide alternatives

Generate only the email response text, no additional formatting or metadata."""

        user_prompt = f"""Original Email:
From: {sender}
Subject: {email_subject}
Body: {email_body}

Generate a professional response to this email."""

        try:
            completion = self.client.chat.completions.create(
                model=self.llm_models[0],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1024
            )
            
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Thank you for your email. We have received your message and will respond shortly."
    
    def _repair_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Attempt to repair malformed JSON"""
        try:
            # Remove markdown code blocks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            # Try parsing again
            return json.loads(text.strip())
        except:
            return None
    
    def _get_fallback_classification(self) -> Dict[str, Any]:
        """Fallback classification when LLM fails"""
        return {
            "filtered": False,
            "priority": "Medium Priority",
            "classification": "Query",
            "sentiment": "Neutral",
            "suggested_responses": [
                "Thank you for your message.",
                "We have received your inquiry and will respond soon.",
                "Please let us know if you need immediate assistance."
            ],
            "other_details": {
                "phone_number": None,
                "address": None,
                "alternate_email": None
            },
            "summary": "Email received and being processed.",
            "metadata": {
                "date": "$CSV_DATE_WILL_BE_FILLED_SEPARATELY"
            }
        }
    
    def generate_embeddings(self, text: str) -> Optional[List[float]]:
        """Generate embeddings using NVIDIA embedding model"""
        
        if not self.client:
            logger.error("NVIDIA client not available")
            return None
        
        try:
            # Truncate text to safe token length (approximately 8000 characters)
            if len(text) > 8000:
                text = text[:8000]
            
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=[text]
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None

# Global client instance
nvidia_client = NVIDIAClient()
