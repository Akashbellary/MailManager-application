import csv
import io
import logging
import re
from typing import List, Dict, Any, Tuple
from datetime import datetime
import uuid
from dateutil import parser
import pytz

from services.nvidia_client import nvidia_client
from services.mongodb_service import mongodb_service
from models import EmailRecord
from utils.date_utils import parse_date_with_timezone
from utils.validators import extract_pii_regex

logger = logging.getLogger(__name__)

class EmailProcessor:
    """Process CSV emails and enrich with AI classification"""
    
    def __init__(self):
        self.batch_size = 5  # Reduced for faster processing
        self.max_retries = 3
    
    def process_csv_upload(self, file_content: bytes) -> Dict[str, Any]:
        """Process uploaded CSV file"""
        try:
            # Decode file content
            content = file_content.decode('utf-8')
            
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(content))
            
            # Validate headers
            required_headers = {'sender', 'subject', 'body', 'sent_date'}
            available_headers = set(csv_reader.fieldnames or [])
            
            # Handle header variations
            header_mapping = self._get_header_mapping(available_headers)
            
            if not all(mapped in available_headers for mapped in header_mapping.values()):
                missing = required_headers - set(header_mapping.keys())
                raise ValueError(f"Missing required columns: {missing}")
            
            # Process rows
            rows = list(csv_reader)
            total_rows = len(rows)
            
            results = {
                "total_rows": total_rows,
                "processed": 0,
                "inserted": 0,
                "failed": 0,
                "sample_ids": [],
                "errors": []
            }
            
            # Process in batches
            for i in range(0, total_rows, self.batch_size):
                batch = rows[i:i + self.batch_size]
                batch_results = self._process_batch(batch, header_mapping)
                
                results["processed"] += len(batch)
                results["inserted"] += batch_results["inserted"]
                results["failed"] += batch_results["failed"]
                results["sample_ids"].extend(batch_results["sample_ids"])
                results["errors"].extend(batch_results["errors"])
                
                logger.info(f"Processed batch {i//self.batch_size + 1}/{(total_rows-1)//self.batch_size + 1}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing CSV: {e}")
            raise
    
    def _get_header_mapping(self, headers: set) -> Dict[str, str]:
        """Map various header names to standard fields"""
        mapping = {}
        headers_lower = {h.lower(): h for h in headers}
        
        # Map sender
        for variant in ['sender', 'from', 'email', 'sender_mail']:
            if variant in headers_lower:
                mapping['sender'] = headers_lower[variant]
                break
        
        # Map subject
        for variant in ['subject', 'email_subject']:
            if variant in headers_lower:
                mapping['subject'] = headers_lower[variant]
                break
        
        # Map body
        for variant in ['body', 'email_body', 'content', 'message']:
            if variant in headers_lower:
                mapping['body'] = headers_lower[variant]
                break
        
        # Map sent_date
        for variant in ['sent_date', 'date', 'timestamp', 'sent_time']:
            if variant in headers_lower:
                mapping['sent_date'] = headers_lower[variant]
                break
        
        return mapping
    
    def _process_batch(self, batch: List[Dict[str, Any]], header_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Process a batch of email rows"""
        results = {
            "inserted": 0,
            "failed": 0,
            "sample_ids": [],
            "errors": []
        }
        
        for row in batch:
            try:
                # Extract CSV fields
                sender = row.get(header_mapping['sender'], '').strip()
                subject = row.get(header_mapping['subject'], '').strip()
                body = row.get(header_mapping['body'], '').strip()
                sent_date = row.get(header_mapping['sent_date'], '').strip()
                
                if not all([sender, subject, body, sent_date]):
                    results["failed"] += 1
                    results["errors"].append("Missing required fields in row")
                    continue
                
                # Parse date
                parsed_date = parse_date_with_timezone(sent_date)
                date_epoch = int(parsed_date.timestamp())
                
                # Classify with LLM
                llm_result = nvidia_client.classify_email(subject, body, sender)
                if not llm_result:
                    results["failed"] += 1
                    results["errors"].append("LLM classification failed")
                    continue
                
                # Extract PII with regex
                pii_data = extract_pii_regex(body)
                
                # Merge PII data
                if llm_result.get("other_details"):
                    for key, value in pii_data.items():
                        if value and not llm_result["other_details"].get(key):
                            llm_result["other_details"][key] = value
                
                # Create email record
                email_record = EmailRecord(
                    sender=sender,
                    email_subject=subject,
                    email_body=body,
                    filtered=llm_result.get("filtered", False),
                    priority=llm_result.get("priority", "Medium Priority"),
                    classification=llm_result.get("classification", "Query"),
                    sentiment=llm_result.get("sentiment", "Neutral"),
                    suggested_responses=llm_result.get("suggested_responses", []),
                    other_details=llm_result.get("other_details", {}),
                    summary=llm_result.get("summary", ""),
                    metadata={
                        "from": sender,
                        "date": parsed_date.isoformat(),
                        "date_epoch": date_epoch
                    }
                )
                
                # Insert into MongoDB
                inserted_id = mongodb_service.insert_email(email_record)
                if not inserted_id:
                    results["failed"] += 1
                    results["errors"].append("Failed to insert into MongoDB")
                    continue
                
                # Generate and store embeddings
                embedding_text = f"{subject}\n\n{body}"
                embedding = nvidia_client.generate_embeddings(embedding_text)
                
                if embedding:
                    # Update MongoDB with embedding info
                    mongodb_service.update_email_embeddings(
                        inserted_id,
                        {
                            "vector": embedding,
                            "model": "nvidia/nv-embed-v1",
                            "dim": len(embedding),
                            "text": embedding_text
                        }
                    )
                
                results["inserted"] += 1
                results["sample_ids"].append(str(inserted_id))
                
            except Exception as e:
                logger.error(f"Error processing row: {e}")
                results["failed"] += 1
                results["errors"].append(str(e))
        
        return results

# Global processor instance
email_processor = EmailProcessor()
