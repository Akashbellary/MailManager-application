import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dateutil import parser as date_parser

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)
    
    return text

def extract_email_addresses(text: str) -> List[str]:
    """Extract email addresses from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)

def extract_phone_numbers(text: str) -> List[str]:
    """Extract phone numbers from text"""
    phone_patterns = [
        r'\b\d{3}-\d{3}-\d{4}\b',  # 123-456-7890
        r'\b\(\d{3}\)\s*\d{3}-\d{4}\b',  # (123) 456-7890
        r'\b\d{3}\s*\d{3}\s*\d{4}\b',  # 123 456 7890
        r'\b\d{10}\b'  # 1234567890
    ]
    
    phone_numbers = []
    for pattern in phone_patterns:
        phone_numbers.extend(re.findall(pattern, text))
    
    return phone_numbers

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime object"""
    if not date_str:
        return None
    
    try:
        return date_parser.parse(date_str)
    except Exception:
        return None

def format_date_for_display(date_str: str) -> str:
    """Format date for display"""
    if not date_str:
        return "N/A"
    
    try:
        dt = parse_date(date_str)
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M")
        return date_str
    except Exception:
        return date_str

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace unsafe characters
    filename = re.sub(r'[^\w\s\-_.]', '', filename)
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    return filename

def validate_csv_headers(headers: List[str]) -> Dict[str, str]:
    """Validate and map CSV headers to expected fields"""
    header_mapping = {}
    
    # Expected header mappings
    sender_headers = ['sender', 'from', 'email', 'sender_mail', 'from_email']
    subject_headers = ['subject', 'email_subject', 'title']
    body_headers = ['body', 'email_body', 'content', 'message', 'text']
    date_headers = ['sent_date', 'date', 'timestamp', 'sent_time', 'created_at']
    
    # Normalize headers for matching
    normalized_headers = [h.lower().strip() for h in headers]
    
    # Find matches
    for i, header in enumerate(normalized_headers):
        if header in sender_headers:
            header_mapping['sender'] = headers[i]
        elif header in subject_headers:
            header_mapping['subject'] = headers[i]
        elif header in body_headers:
            header_mapping['body'] = headers[i]
        elif header in date_headers:
            header_mapping['date'] = headers[i]
    
    return header_mapping

def create_pagination_info(page: int, per_page: int, total: int) -> Dict[str, Any]:
    """Create pagination information"""
    total_pages = (total + per_page - 1) // per_page
    
    return {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < total_pages else None
    }

def parse_filter_params(request_args) -> Dict[str, List[str]]:
    """Parse filter parameters from request arguments"""
    filters = {}
    
    # Handle multi-select filters
    for key in ['priority', 'sentiment', 'classification']:
        if hasattr(request_args, 'getlist'):
            values = request_args.getlist(key)
        else:
            # Fallback for regular dict
            value = request_args.get(key)
            values = [value] if value else []
        
        if values:
            # Remove empty values
            values = [v for v in values if v and v.strip()]
            if values:
                filters[key] = values
    
    return filters

def build_mongo_filter(filters: Dict[str, List[str]], search_query: Optional[str] = None) -> Dict[str, Any]:
    """Build MongoDB filter from parsed filters"""
    mongo_filter = {}
    
    # Add filter conditions
    for field, values in filters.items():
        if len(values) == 1:
            mongo_filter[field] = values[0]
        else:
            mongo_filter[field] = {'$in': values}
    
    # Add search query if provided
    if search_query and search_query.strip():
        search_conditions = [
            {'sender': {'$regex': search_query, '$options': 'i'}},
            {'email_subject': {'$regex': search_query, '$options': 'i'}},
            {'email_body': {'$regex': search_query, '$options': 'i'}},
            {'classification': {'$regex': search_query, '$options': 'i'}}
        ]
        
        if mongo_filter:
            # Combine with existing filters using AND
            mongo_filter = {'$and': [mongo_filter, {'$or': search_conditions}]}
        else:
            mongo_filter = {'$or': search_conditions}
    
    return mongo_filter

def calculate_stats(emails: List[Dict]) -> Dict[str, Any]:
    """Calculate statistics from emails"""
    if not emails:
        return {
            'total_emails': 0,
            'priority_stats': {'High Priority': 0, 'Medium Priority': 0, 'Low Priority': 0},
            'sentiment_stats': {'Positive': 0, 'Neutral': 0, 'Negative': 0},
            'classification_stats': {},
            'filtered_count': 0
        }
    
    stats = {
        'total_emails': len(emails),
        'priority_stats': {'High Priority': 0, 'Medium Priority': 0, 'Low Priority': 0},
        'sentiment_stats': {'Positive': 0, 'Neutral': 0, 'Negative': 0},
        'classification_stats': {},
        'filtered_count': 0
    }
    
    for email in emails:
        # Priority stats
        priority = email.get('priority', 'Low Priority')
        if priority in stats['priority_stats']:
            stats['priority_stats'][priority] += 1
        
        # Sentiment stats
        sentiment = email.get('sentiment', 'Neutral')
        if sentiment in stats['sentiment_stats']:
            stats['sentiment_stats'][sentiment] += 1
        
        # Classification stats
        classification = email.get('classification', 'General')
        stats['classification_stats'][classification] = stats['classification_stats'].get(classification, 0) + 1
        
        # Filtered count
        if email.get('filtered', False):
            stats['filtered_count'] += 1
    
    return stats

def safe_json_encode(data: Any) -> str:
    """Safely encode data to JSON"""
    try:
        return json.dumps(data, default=str)
    except Exception:
        return "{}"
