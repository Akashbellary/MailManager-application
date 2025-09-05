import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.nvidia_client import nvidia_client
from services.mongodb_service import mongodb_service
from models import SearchResult, EmailRecord

logger = logging.getLogger(__name__)

class SearchService:
    """Service for handling email search operations"""
    
    def __init__(self):
        pass
    
    def execute_search(self, query: str, k: int = 25, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute search based on query"""
        try:
            logger.info(f"Executing search for query: {query}")
            
            # Check if it's a simple filter query or semantic search
            if self._is_filter_query(query):
                return self._execute_filter_search(query, k, filters)
            else:
                return self._execute_semantic_search(query, k, filters)
                
        except Exception as e:
            logger.error(f"Error executing search: {e}")
            return []
    
    def _is_filter_query(self, query: str) -> bool:
        """Determine if query is a simple filter query"""
        filter_keywords = ['priority:', 'sentiment:', 'from:', 'classification:', 'high', 'medium', 'low', 'positive', 'negative', 'neutral']
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in filter_keywords)
    
    def _execute_filter_search(self, query: str, k: int, filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute filter-based search"""
        try:
            # Parse query for filters
            mongo_filter = self._parse_filter_query(query)
            
            # Merge with existing filters
            if filters:
                mongo_filter.update(filters)
            
            # Execute MongoDB query
            result = mongodb_service.get_emails(
                page=1,
                page_size=k,
                filters=mongo_filter,
                sort=[("metadata.date_epoch", -1)]
            )
            
            # Format results
            formatted_results = []
            for email in result["data"]:
                search_result = {
                    "email_record": email,
                    "score": 1.0,  # Perfect match for filter queries
                    "highlights": self._generate_highlights(email, query)
                }
                formatted_results.append(search_result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in filter search: {e}")
            return []
    
    def _execute_semantic_search(self, query: str, k: int, filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute semantic vector search"""
        try:
            # Get embedding for query
            query_embedding = nvidia_client.generate_embeddings(query)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return self._fallback_text_search(query, k, filters)
            
            # Search vectors in MongoDB
            vector_results = mongodb_service.vector_search(
                query_vector=query_embedding,
                k=k,
                filters=filters
            )
            
            # Format results
            formatted_results = []
            for result in vector_results:
                search_result = {
                    "email_record": result,
                    "score": result.get("score", 0.5),
                    "highlights": self._generate_highlights(result, query)
                }
                formatted_results.append(search_result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return self._fallback_text_search(query, k, filters)
    
    def _fallback_text_search(self, query: str, k: int, filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback to MongoDB text search"""
        try:
            # Use MongoDB text search
            mongo_filter = {"$text": {"$search": query}}
            if filters:
                mongo_filter.update(filters)
            
            result = mongodb_service.get_emails(
                page=1,
                page_size=k,
                filters=mongo_filter,
                sort=[("score", {"$meta": "textScore"})]
            )
            
            formatted_results = []
            for email in result["data"]:
                search_result = {
                    "email_record": email,
                    "score": 0.5,  # Default score for text search
                    "highlights": self._generate_highlights(email, query)
                }
                formatted_results.append(search_result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in fallback text search: {e}")
            return []
    
    def _parse_filter_query(self, query: str) -> Dict[str, Any]:
        """Parse natural language query into MongoDB filter"""
        filters = {}
        query_lower = query.lower()
        
        # Priority filters
        if 'high priority' in query_lower or 'urgent' in query_lower:
            filters['priority'] = 'High Priority'
        elif 'low priority' in query_lower:
            filters['priority'] = 'Low Priority'
        elif 'medium priority' in query_lower:
            filters['priority'] = 'Medium Priority'
        
        # Sentiment filters
        if 'positive' in query_lower:
            filters['sentiment'] = 'Positive'
        elif 'negative' in query_lower:
            filters['sentiment'] = 'Negative'
        elif 'neutral' in query_lower:
            filters['sentiment'] = 'Neutral'
        
        # Classification filters
        if 'support' in query_lower:
            filters['classification'] = 'Support'
        elif 'query' in query_lower or 'question' in query_lower:
            filters['classification'] = 'Query'
        elif 'request' in query_lower:
            filters['classification'] = 'Request'
        elif 'help' in query_lower:
            filters['classification'] = 'Help'
        
        # Filtered emails
        if 'spam' in query_lower or 'filtered' in query_lower:
            filters['filtered'] = True
        elif 'not spam' in query_lower or 'unfiltered' in query_lower:
            filters['filtered'] = False
        
        return filters
    
    def _generate_highlights(self, email: Dict[str, Any], query: str) -> List[str]:
        """Generate text highlights for search results"""
        if not query:
            return []
        
        highlights = []
        
        try:
            # Extract subject and body
            subject = email.get("email_subject", "")
            body = email.get("email_body", "")
            
            # Simple highlighting - find query terms in subject/body
            query_terms = query.lower().split()
            
            # Check subject
            if any(term in subject.lower() for term in query_terms):
                highlight = subject[:100] + "..." if len(subject) > 100 else subject
                highlights.append(f"Subject: {highlight}")
            
            # Check body
            body_lower = body.lower()
            for term in query_terms:
                if term in body_lower:
                    # Find the term and extract surrounding context
                    start_idx = body_lower.find(term)
                    if start_idx >= 0:
                        start = max(0, start_idx - 50)
                        end = min(len(body), start_idx + len(term) + 50)
                        snippet = body[start:end]
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(body):
                            snippet = snippet + "..."
                        highlights.append(snippet)
                        break  # Only one body highlight per query
            
            return highlights[:3]  # Limit to 3 highlights
            
        except Exception as e:
            logger.error(f"Error generating highlights: {e}")
            return []

# Global service instance
search_service = SearchService()
