import logging
import numpy as np
from typing import Dict, List, Optional, Any
from emailflow.utils.database import find_emails, count_emails, get_emails_collection
from emailflow.services.ai_service import ai_service
from emailflow.utils.helpers import build_mongo_filter

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        self.similarity_threshold = 0.7
    
    def search_emails(self, query: str, filters: Optional[Dict[str, List[str]]] = None, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Search emails using natural language query and filters
        """
        try:
            # Interpret natural language query
            query_interpretation = ai_service.interpret_search_query(query)
            
            # Combine interpreted filters with provided filters
            combined_filters = filters or {}
            interpreted_filters = query_interpretation.get('filters', {})
            
            for key, values in interpreted_filters.items():
                if key in combined_filters:
                    # Merge lists and remove duplicates
                    combined_filters[key] = list(set(combined_filters[key] + values))
                else:
                    combined_filters[key] = values
            
            # Build search terms
            search_terms = query_interpretation.get('search_terms', [])
            sender_filters = query_interpretation.get('sender_filters', [])
            
            # If we have semantic search capability, use vector search
            if search_terms or query.strip():
                return self._semantic_search(query, combined_filters, sender_filters, page, per_page)
            else:
                # Use filter-only search
                return self._filter_search(combined_filters, page, per_page)
                
        except Exception as e:
            logger.error(f"Error in search_emails: {e}")
            raise Exception(f"Failed to perform search: {str(e)}")
    
    def _semantic_search(self, query: str, filters: Dict[str, List[str]], sender_filters: List[str], page: int, per_page: int) -> Dict[str, Any]:
        """
        Perform semantic search using embeddings
        """
        try:
            # Generate query embedding
            query_embeddings = ai_service.generate_embeddings([query])
            
            if not query_embeddings:
                # Fallback to text search
                return self._text_search(query, filters, sender_filters, page, per_page)
                
            query_embedding = query_embeddings[0]
            
            # Get all emails with embeddings for similarity comparison
            # Note: In production, you'd use a vector database like Pinecone or Weaviate
            all_emails = find_emails({}, skip=0, limit=1000)  # Limit for performance
            
            # Calculate similarities
            scored_emails = []
            for email in all_emails:
                if 'embeddings' in email and 'vector' in email['embeddings']:
                    similarity = self._calculate_similarity(query_embedding, email['embeddings']['vector'])
                    if similarity >= self.similarity_threshold:
                        email['similarity_score'] = similarity
                        scored_emails.append(email)
            
            # Sort by similarity
            scored_emails.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Apply filters
            filtered_emails = self._apply_filters(scored_emails, filters, sender_filters)
            
            # Apply pagination
            skip = (page - 1) * per_page
            paginated_emails = filtered_emails[skip:skip + per_page]
            
            return {
                'emails': paginated_emails,
                'total': len(filtered_emails),
                'page': page,
                'per_page': per_page,
                'query_interpretation': ai_service.interpret_search_query(query)
            }
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            raise Exception(f"Semantic search failed: {str(e)}")
    
    def _text_search(self, query: str, filters: Dict[str, List[str]], sender_filters: List[str], page: int, per_page: int) -> Dict[str, Any]:
        """
        Perform text-based search
        """
        try:
            # Build MongoDB filter
            search_query = query
            if sender_filters:
                # Add sender filters to search query
                search_query = f"{query} {' '.join(sender_filters)}"
            
            mongo_filter = build_mongo_filter(filters, search_query)
            
            # Add sender-specific filters
            if sender_filters:
                sender_conditions = []
                for sender in sender_filters:
                    sender_conditions.append({'sender': {'$regex': sender, '$options': 'i'}})
                
                if mongo_filter:
                    if '$and' in mongo_filter:
                        mongo_filter['$and'].append({'$or': sender_conditions})
                    else:
                        mongo_filter = {'$and': [mongo_filter, {'$or': sender_conditions}]}
                else:
                    mongo_filter = {'$or': sender_conditions}
            
            # Get total count
            total = count_emails(mongo_filter)
            
            # Get paginated results
            skip = (page - 1) * per_page
            emails = find_emails(mongo_filter, skip=skip, limit=per_page)
            
            return {
                'emails': emails,
                'total': total,
                'page': page,
                'per_page': per_page,
                'query_interpretation': ai_service.interpret_search_query(query)
            }
            
        except Exception as e:
            logger.error(f"Error in text search: {e}")
            raise Exception(f"Text search failed: {str(e)}")
    
    def _filter_search(self, filters: Dict[str, List[str]], page: int, per_page: int) -> Dict[str, Any]:
        """
        Perform filter-only search
        """
        try:
            mongo_filter = build_mongo_filter(filters)
            
            # Get total count
            total = count_emails(mongo_filter)
            
            # Get paginated results
            skip = (page - 1) * per_page
            emails = find_emails(mongo_filter, skip=skip, limit=per_page)
            
            return {
                'emails': emails,
                'total': total,
                'page': page,
                'per_page': per_page,
                'query_interpretation': {'filters': filters, 'search_terms': [], 'sender_filters': []}
            }
            
        except Exception as e:
            logger.error(f"Error in filter search: {e}")
            raise Exception(f"Filter search failed: {str(e)}")
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def _apply_filters(self, emails: List[Dict], filters: Dict[str, List[str]], sender_filters: List[str]) -> List[Dict]:
        """
        Apply filters to email list
        """
        filtered_emails = emails.copy()
        
        # Apply field filters
        for field, values in filters.items():
            if values:
                filtered_emails = [email for email in filtered_emails if email.get(field) in values]
        
        # Apply sender filters
        if sender_filters:
            filtered_emails = [
                email for email in filtered_emails
                if any(sender.lower() in email.get('sender', '').lower() for sender in sender_filters)
            ]
        
        return filtered_emails
    
    def get_search_suggestions(self, query: str) -> List[str]:
        """
        Get search suggestions based on query
        """
        try:
            suggestions = []
            
            # Add common search patterns
            if 'negative' in query.lower():
                suggestions.extend(['negative sentiment emails', 'complaints', 'angry customers'])
            elif 'positive' in query.lower():
                suggestions.extend(['positive feedback', 'satisfied customers', 'thank you emails'])
            elif 'high' in query.lower() or 'urgent' in query.lower():
                suggestions.extend(['high priority emails', 'urgent requests', 'critical issues'])
            elif 'support' in query.lower():
                suggestions.extend(['support tickets', 'help requests', 'technical issues'])
            
            # Add sender-based suggestions if query contains names
            words = query.split()
            for word in words:
                if len(word) > 2 and word.isalpha():
                    suggestions.append(f'emails from {word}')
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []

# Global search service instance
search_service = SearchService()