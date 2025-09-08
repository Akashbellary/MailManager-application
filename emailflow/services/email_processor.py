# import csv
# import logging
# import json
# from datetime import datetime
# from typing import Dict, List, Optional, Generator, Any
# from io import StringIO
# from emailflow.utils.database import insert_email, update_progress, insert_progress
# from emailflow.utils.helpers import clean_text, extract_email_addresses, extract_phone_numbers, parse_date, validate_csv_headers
# from emailflow.services.ai_service import ai_service
# from emailflow.models import Email, UploadProgress

# logger = logging.getLogger(__name__)

# from bson import ObjectId
# import uuid

# def process_email(email_data):
#     # Ensure document has an _id
#     if '_id' not in email_data:
#         email_data['_id'] = ObjectId()  # or str(uuid.uuid4()) for string IDs
    
#     # Then insert the document
#     # db.get_collection('emails').insert_one(email_data)

# from bson import ObjectId

# # When inserting emails, ensure they have unique IDs
# email_document['_id'] = ObjectId()  # or use uuid.uuid4() for string IDs

# def generate_embeddings(self, texts):
#     """Generate embeddings for texts using NVIDIA API"""
#     try:
#         if not self.client:
#             raise Exception("AI client not initialized")
        
#         # Add input_type parameter for asymmetric models
#         response = self.client.embeddings.create(
#             model="nvidia/nv-embedqa-e5-v5",
#             input=texts,
#             encoding_format="float",
#             input_type="passage"  # Required for asymmetric models - can also be "query"
#         )
        
#         return [item.embedding for item in response.data]
    
#     except Exception as e:
#         logger.error(f"Error generating embeddings: {e}")
#         raise

# class EmailProcessor:
#     def __init__(self):
#         self.supported_encodings = ['utf-8', 'latin-1', 'cp1252']
    
#     def process_csv_file(self, file_path: str, filename: str) -> str:
#         """Process CSV file and return progress ID"""
#         progress_data = UploadProgress({
#             'filename': filename,
#             'total_rows': 0,
#             'processed_rows': 0,
#             'status': 'processing',
#             'error_message': ''
#         }).to_dict()
        
#         progress_id = insert_progress(progress_data)
        
#         try:
#             # First pass: count total rows
#             total_rows = self._count_csv_rows(file_path)
#             update_progress(progress_id, {'total_rows': total_rows})
            
#             # Second pass: process emails
#             self._process_csv_emails(file_path, progress_id)
            
#             # Mark as completed
#             update_progress(progress_id, {
#                 'status': 'completed',
#                 'updated_at': datetime.utcnow().isoformat()
#             })
            
#         except Exception as e:
#             logger.error(f"Error processing CSV file: {e}")
#             update_progress(progress_id, {
#                 'status': 'failed',
#                 'error_message': str(e),
#                 'updated_at': datetime.utcnow().isoformat()
#             })
        
#         return progress_id
    
#     def _count_csv_rows(self, file_path: str) -> int:
#         """Count total rows in CSV file"""
#         try:
#             for encoding in self.supported_encodings:
#                 try:
#                     with open(file_path, 'r', encoding=encoding) as file:
#                         csv_reader = csv.reader(file)
#                         next(csv_reader)  # Skip header
#                         return sum(1 for _ in csv_reader)
#                 except UnicodeDecodeError:
#                     continue
            
#             raise Exception("Unable to decode CSV file with supported encodings")
            
#         except Exception as e:
#             logger.error(f"Error counting CSV rows: {e}")
#             raise
    
#     def _process_csv_emails(self, file_path: str, progress_id: str):
#         """Process emails from CSV file"""
#         try:
#             for encoding in self.supported_encodings:
#                 try:
#                     with open(file_path, 'r', encoding=encoding) as file:
#                         csv_reader = csv.DictReader(file)
#                         headers = csv_reader.fieldnames
                        
#                         # Validate headers
#                         if not headers:
#                             raise Exception("CSV file has no headers")
#                         header_mapping = validate_csv_headers(list(headers))
#                         if not all(key in header_mapping for key in ['sender', 'subject', 'body']):
#                             raise Exception("CSV must contain sender, subject, and body columns")
                        
#                         processed_count = 0
                        
#                         for row in csv_reader:
#                             try:
#                                 email_data = self._process_email_row(row, header_mapping)
#                                 insert_email(email_data)
                                
#                                 processed_count += 1
                                
#                                 # Update progress every 10 emails
#                                 if processed_count % 10 == 0:
#                                     update_progress(progress_id, {
#                                         'processed_rows': processed_count,
#                                         'updated_at': datetime.utcnow().isoformat()
#                                     })
                                
#                             except Exception as e:
#                                 logger.error(f"Error processing email row: {e}")
#                                 continue
                        
#                         # Final progress update
#                         update_progress(progress_id, {
#                             'processed_rows': processed_count,
#                             'updated_at': datetime.utcnow().isoformat()
#                         })
                        
#                         return
                        
#                 except UnicodeDecodeError:
#                     continue
            
#             raise Exception("Unable to decode CSV file with supported encodings")
            
#         except Exception as e:
#             logger.error(f"Error processing CSV emails: {e}")
#             raise
    
#     def _process_email_row(self, row: Dict[str, str], header_mapping: Dict[str, str]) -> Dict:
#         """Process individual email row"""
#         try:
#             # Extract basic fields
#             sender = clean_text(row.get(header_mapping['sender'], ''))
#             subject = clean_text(row.get(header_mapping['subject'], ''))
#             body = clean_text(row.get(header_mapping['body'], ''))
            
#             if not sender or not subject or not body:
#                 raise ValueError("Missing required fields: sender, subject, or body")
            
#             # Parse date
#             date_str = row.get(header_mapping.get('date', ''), '')
#             parsed_date = parse_date(date_str)
            
#             # AI Classification
#             classification_result = ai_service.classify_email(subject, body)
            
#             # Extract additional details
#             other_details = self._extract_details(body)
            
#             # Generate embeddings
#             embeddings_data = {}
#             text_for_embedding = f"{subject} {body}"
#             embeddings = ai_service.generate_embeddings(text_for_embedding)
            
#             if embeddings:
#                 embeddings_data = {
#                     'vector': embeddings,
#                     'model': 'nvidia/nv-embedqa-e5-v5',
#                     'dim': len(embeddings)
#                 }
            
#             # Generate suggested responses
#             suggested_responses = []
#             response = ai_service.generate_response(subject, body, classification_result['classification'])
#             if response:
#                 suggested_responses.append(response)
            
#             # Create email document
#             email_data = Email({
#                 'sender': sender,
#                 'email_subject': subject,
#                 'email_body': body,
#                 'priority': classification_result['priority'],
#                 'sentiment': classification_result['sentiment'],
#                 'classification': classification_result['classification'],
#                 'summary': classification_result['summary'],
#                 'filtered': False,  # TODO: Implement spam filtering
#                 'metadata': {
#                     'date': parsed_date.isoformat() if parsed_date else date_str,
#                     'date_epoch': int(parsed_date.timestamp()) if parsed_date else None,
#                     'original_row': dict(row)
#                 },
#                 'other_details': other_details,
#                 'suggested_responses': suggested_responses,
#                 'embeddings': embeddings_data,
#                 'created_at': datetime.utcnow().isoformat(),
#                 'updated_at': datetime.utcnow().isoformat()
#             }).to_dict()
            
#             return email_data
            
#         except Exception as e:
#             logger.error(f"Error processing email row: {e}")
#             raise
    
#     def _extract_details(self, text: str) -> Dict[str, Any]:
#         """Extract additional details from email text"""
#         details = {}
        
#         # Extract email addresses
#         emails = extract_email_addresses(text)
#         if emails:
#             details['alternate_email'] = emails[0]  # Take first found email
        
#         # Extract phone numbers
#         phones = extract_phone_numbers(text)
#         if phones:
#             details['phone_number'] = phones[0]  # Take first found phone
        
#         # Extract potential addresses (simple pattern)
#         address_patterns = [
#             r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)',
#             r'[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}'
#         ]
        
#         import re
#         for pattern in address_patterns:
#             matches = re.findall(pattern, text, re.IGNORECASE)
#             if matches:
#                 details['address'] = matches[0]
#                 break
        
#         return details

# # Global email processor instance
# email_processor = EmailProcessor()





#--------------------------------------------------------------------------------------------------------------------------------------------


# import csv
# import logging
# import json
# from datetime import datetime
# from typing import Dict, List, Optional, Generator, Any
# from io import StringIO
# from emailflow.utils.database import insert_email, update_progress, insert_progress
# from emailflow.utils.helpers import clean_text, extract_email_addresses, extract_phone_numbers, parse_date, validate_csv_headers
# from emailflow.services.ai_service import ai_service
# from emailflow.models import Email, UploadProgress

# logger = logging.getLogger(__name__)

# from bson import ObjectId
# import uuid

# class EmailProcessor:
#     def __init__(self):
#         self.supported_encodings = ['utf-8', 'latin-1', 'cp1252']
    
#     def process_csv_file(self, file_path: str, filename: str) -> str:
#         """Process CSV file and return progress ID"""
#         progress_data = UploadProgress({
#             'filename': filename,
#             'total_rows': 0,
#             'processed_rows': 0,
#             'status': 'processing',
#             'error_message': ''
#         }).to_dict()
        
#         progress_id = insert_progress(progress_data)
        
#         try:
#             # First pass: count total rows
#             total_rows = self._count_csv_rows(file_path)
#             update_progress(progress_id, {'total_rows': total_rows})
            
#             # Second pass: process emails
#             self._process_csv_emails(file_path, progress_id)
            
#             # Mark as completed
#             update_progress(progress_id, {
#                 'status': 'completed',
#                 'updated_at': datetime.utcnow().isoformat()
#             })
            
#         except Exception as e:
#             logger.error(f"Error processing CSV file: {e}")
#             update_progress(progress_id, {
#                 'status': 'failed',
#                 'error_message': str(e),
#                 'updated_at': datetime.utcnow().isoformat()
#             })
        
#         return progress_id
    
#     def _count_csv_rows(self, file_path: str) -> int:
#         """Count total rows in CSV file"""
#         try:
#             for encoding in self.supported_encodings:
#                 try:
#                     with open(file_path, 'r', encoding=encoding) as file:
#                         csv_reader = csv.reader(file)
#                         next(csv_reader)  # Skip header
#                         return sum(1 for _ in csv_reader)
#                 except UnicodeDecodeError:
#                     continue
            
#             raise Exception("Unable to decode CSV file with supported encodings")
            
#         except Exception as e:
#             logger.error(f"Error counting CSV rows: {e}")
#             raise
    
#     def _process_csv_emails(self, file_path: str, progress_id: str):
#         """Process emails from CSV file"""
#         try:
#             for encoding in self.supported_encodings:
#                 try:
#                     with open(file_path, 'r', encoding=encoding) as file:
#                         csv_reader = csv.DictReader(file)
#                         headers = csv_reader.fieldnames
                        
#                         # Validate headers
#                         if not headers:
#                             raise Exception("CSV file has no headers")
#                         header_mapping = validate_csv_headers(list(headers))
#                         if not all(key in header_mapping for key in ['sender', 'subject', 'body']):
#                             raise Exception("CSV must contain sender, subject, and body columns")
                        
#                         processed_count = 0
                        
#                         for row in csv_reader:
#                             try:
#                                 email_data = self._process_email_row(row, header_mapping)
#                                 insert_email(email_data)
                                
#                                 processed_count += 1
                                
#                                 # Update progress every 10 emails
#                                 if processed_count % 10 == 0:
#                                     update_progress(progress_id, {
#                                         'processed_rows': processed_count,
#                                         'updated_at': datetime.utcnow().isoformat()
#                                     })
                                
#                             except Exception as e:
#                                 logger.error(f"Error processing email row: {e}")
#                                 continue
                        
#                         # Final progress update
#                         update_progress(progress_id, {
#                             'processed_rows': processed_count,
#                             'updated_at': datetime.utcnow().isoformat()
#                         })
                        
#                         return
                        
#                 except UnicodeDecodeError:
#                     continue
            
#             raise Exception("Unable to decode CSV file with supported encodings")
            
#         except Exception as e:
#             logger.error(f"Error processing CSV emails: {e}")
#             raise
    
#     def _process_email_row(self, row: Dict[str, str], header_mapping: Dict[str, str]) -> Dict:
#         """Process individual email row"""
#         try:
#             # Extract basic fields
#             sender = clean_text(row.get(header_mapping['sender'], ''))
#             subject = clean_text(row.get(header_mapping['subject'], ''))
#             body = clean_text(row.get(header_mapping['body'], ''))
            
#             if not sender or not subject or not body:
#                 raise ValueError("Missing required fields: sender, subject, or body")
            
#             # Parse date
#             date_str = row.get(header_mapping.get('date', ''), '')
#             parsed_date = parse_date(date_str)
            
#             # AI Classification
#             classification_result = ai_service.classify_email(subject, body)
            
#             # Extract additional details
#             other_details = self._extract_details(body)
            
#             # Generate embeddings
#             embeddings_data = {}
#             text_for_embedding = f"{subject} {body}"
#             embeddings = ai_service.generate_embeddings([text_for_embedding])  # Pass as list
            
#             if embeddings:
#                 embeddings_data = {
#                     'vector': embeddings[0],  # Get first embedding
#                     'model': 'nvidia/nv-embedqa-e5-v5',
#                     'dim': len(embeddings[0])
#                 }
            
#             # Generate suggested responses
#             suggested_responses = []
#             response = ai_service.generate_response(subject, body, classification_result['classification'])
#             if response:
#                 suggested_responses.append(response)
            
#             # Create email document with unique _id
#             email_data = Email({
#                 'sender': sender,
#                 'email_subject': subject,
#                 'email_body': body,
#                 'priority': classification_result['priority'],
#                 'sentiment': classification_result['sentiment'],
#                 'classification': classification_result['classification'],
#                 'summary': classification_result['summary'],
#                 'filtered': False,  # TODO: Implement spam filtering
#                 'metadata': {
#                     'date': parsed_date.isoformat() if parsed_date else date_str,
#                     'date_epoch': int(parsed_date.timestamp()) if parsed_date else None,
#                     'original_row': dict(row)
#                 },
#                 'other_details': other_details,
#                 'suggested_responses': suggested_responses,
#                 'embeddings': embeddings_data,
#                 'created_at': datetime.utcnow().isoformat(),
#                 'updated_at': datetime.utcnow().isoformat()
#             }).to_dict()
            
#             # Ensure document has a unique _id
#             if '_id' not in email_data or email_data['_id'] is None:
#                 email_data['_id'] = ObjectId()
            
#             return email_data
            
#         except Exception as e:
#             logger.error(f"Error processing email row: {e}")
#             raise
    
#     def _extract_details(self, text: str) -> Dict[str, Any]:
#         """Extract additional details from email text"""
#         details = {}
        
#         # Extract email addresses
#         emails = extract_email_addresses(text)
#         if emails:
#             details['alternate_email'] = emails[0]  # Take first found email
        
#         # Extract phone numbers
#         phones = extract_phone_numbers(text)
#         if phones:
#             details['phone_number'] = phones[0]  # Take first found phone
        
#         # Extract potential addresses (simple pattern)
#         address_patterns = [
#             r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)',
#             r'[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}'
#         ]
        
#         import re
#         for pattern in address_patterns:
#             matches = re.findall(pattern, text, re.IGNORECASE)
#             if matches:
#                 details['address'] = matches[0]
#                 break
        
#         return details

# # Global email processor instance
# email_processor = EmailProcessor()


#-------------------------------------------------------------------------------------------------------------------------------------------


# import csv
# import logging
# import json
# from datetime import datetime
# from typing import Dict, List, Optional, Generator, Any
# from io import StringIO
# from emailflow.utils.database import insert_email, update_progress, insert_progress
# from emailflow.utils.helpers import clean_text, extract_email_addresses, extract_phone_numbers, parse_date, validate_csv_headers
# from emailflow.services.ai_service import ai_service
# from emailflow.models import Email, UploadProgress

# logger = logging.getLogger(__name__)

# from bson import ObjectId
# import uuid

# class EmailProcessor:
#     def __init__(self):
#         self.supported_encodings = ['utf-8', 'latin-1', 'cp1252']
    
#     def process_csv_file(self, file_path: str, filename: str) -> str:
#         """Process CSV file and return progress ID"""
#         progress_data = UploadProgress({
#             'filename': filename,
#             'total_rows': 0,
#             'processed_rows': 0,
#             'status': 'processing',
#             'error_message': ''
#         }).to_dict()
        
#         progress_id = insert_progress(progress_data)
        
#         try:
#             # First pass: count total rows
#             total_rows = self._count_csv_rows(file_path)
#             update_progress(progress_id, {'total_rows': total_rows})
            
#             # Second pass: process emails
#             self._process_csv_emails(file_path, progress_id)
            
#             # Mark as completed
#             update_progress(progress_id, {
#                 'status': 'completed',
#                 'updated_at': datetime.utcnow().isoformat()
#             })
            
#         except Exception as e:
#             logger.error(f"Error processing CSV file: {e}")
#             update_progress(progress_id, {
#                 'status': 'failed',
#                 'error_message': str(e),
#                 'updated_at': datetime.utcnow().isoformat()
#             })
        
#         return progress_id
    
#     def _count_csv_rows(self, file_path: str) -> int:
#         """Count total rows in CSV file"""
#         try:
#             for encoding in self.supported_encodings:
#                 try:
#                     with open(file_path, 'r', encoding=encoding) as file:
#                         csv_reader = csv.reader(file)
#                         next(csv_reader)  # Skip header
#                         return sum(1 for _ in csv_reader)
#                 except UnicodeDecodeError:
#                     continue
            
#             raise Exception("Unable to decode CSV file with supported encodings")
            
#         except Exception as e:
#             logger.error(f"Error counting CSV rows: {e}")
#             raise
    
#     def _process_csv_emails(self, file_path: str, progress_id: str):
#         """Process emails from CSV file"""
#         try:
#             for encoding in self.supported_encodings:
#                 try:
#                     with open(file_path, 'r', encoding=encoding) as file:
#                         csv_reader = csv.DictReader(file)
#                         headers = csv_reader.fieldnames
                        
#                         # Validate headers
#                         if not headers:
#                             raise Exception("CSV file has no headers")
#                         header_mapping = validate_csv_headers(list(headers))
#                         if not all(key in header_mapping for key in ['sender', 'subject', 'body']):
#                             raise Exception("CSV must contain sender, subject, and body columns")
                        
#                         processed_count = 0
                        
#                         for row in csv_reader:
#                             try:
#                                 email_data = self._process_email_row(row, header_mapping)
#                                 insert_email(email_data)
                                
#                                 processed_count += 1
                                
#                                 # Update progress every 10 emails
#                                 if processed_count % 10 == 0:
#                                     update_progress(progress_id, {
#                                         'processed_rows': processed_count,
#                                         'updated_at': datetime.utcnow().isoformat()
#                                     })
                                
#                             except Exception as e:
#                                 logger.error(f"Error processing email row: {e}")
#                                 continue
                        
#                         # Final progress update
#                         update_progress(progress_id, {
#                             'processed_rows': processed_count,
#                             'updated_at': datetime.utcnow().isoformat()
#                         })
                        
#                         return
                        
#                 except UnicodeDecodeError:
#                     continue
            
#             raise Exception("Unable to decode CSV file with supported encodings")
            
#         except Exception as e:
#             logger.error(f"Error processing CSV emails: {e}")
#             raise
    
#     def _process_email_row(self, row: Dict[str, str], header_mapping: Dict[str, str]) -> Dict:
#         """Process individual email row"""
#         try:
#             # Extract basic fields
#             sender = clean_text(row.get(header_mapping['sender'], ''))
#             subject = clean_text(row.get(header_mapping['subject'], ''))
#             body = clean_text(row.get(header_mapping['body'], ''))
            
#             if not sender or not subject or not body:
#                 raise ValueError("Missing required fields: sender, subject, or body")
            
#             # Parse date
#             date_str = row.get(header_mapping.get('date', ''), '')
#             parsed_date = parse_date(date_str)
            
#             # AI Classification
#             classification_result = ai_service.classify_email(subject, body)
            
#             # Extract additional details
#             other_details = self._extract_details(body)
            
#             # Generate embeddings
#             embeddings_data = {}
#             text_for_embedding = f"{subject} {body}"
#             embeddings = ai_service.generate_embeddings([text_for_embedding])  # Pass as list
            
#             if embeddings:
#                 embeddings_data = {
#                     'vector': embeddings[0],  # Get first embedding
#                     'model': 'nvidia/nv-embedqa-e5-v5',
#                     'dim': len(embeddings[0])
#                 }
            
#             # Generate suggested responses
#             suggested_responses = []
#             response = ai_service.generate_response(subject, body, classification_result['classification'])
#             if response:
#                 suggested_responses.append(response)
            
#             # Create email document with unique _id
#             email_data = Email({
#                 'sender': sender,
#                 'email_subject': subject,
#                 'email_body': body,
#                 'priority': classification_result['priority'],
#                 'sentiment': classification_result['sentiment'],
#                 'classification': classification_result['classification'],
#                 'summary': classification_result['summary'],
#                 'filtered': False,  # TODO: Implement spam filtering
#                 'metadata': {
#                     'date': parsed_date.isoformat() if parsed_date else date_str,
#                     'date_epoch': int(parsed_date.timestamp()) if parsed_date else None,
#                     'original_row': dict(row)
#                 },
#                 'other_details': other_details,
#                 'suggested_responses': suggested_responses,
#                 'embeddings': embeddings_data,
#                 'created_at': datetime.utcnow().isoformat(),
#                 'updated_at': datetime.utcnow().isoformat()
#             }).to_dict()
            
#             # Ensure document has a unique _id
#             if '_id' not in email_data or email_data['_id'] is None:
#                 email_data['_id'] = ObjectId()
            
#             return email_data
            
#         except Exception as e:
#             logger.error(f"Error processing email row: {e}")
#             raise
    
#     def _extract_details(self, text: str) -> Dict[str, Any]:
#         """Extract additional details from email text"""
#         details = {}
        
#         # Extract email addresses
#         emails = extract_email_addresses(text)
#         if emails:
#             details['alternate_email'] = emails[0]  # Take first found email
        
#         # Extract phone numbers
#         phones = extract_phone_numbers(text)
#         if phones:
#             details['phone_number'] = phones[0]  # Take first found phone
        
#         # Extract potential addresses (simple pattern)
#         address_patterns = [
#             r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)',
#             r'[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}'
#         ]
        
#         import re
#         for pattern in address_patterns:
#             matches = re.findall(pattern, text, re.IGNORECASE)
#             if matches:
#                 details['address'] = matches[0]
#                 break
        
#         return details

# # Global email processor instance
# email_processor = EmailProcessor()


#----------------------------------------------------------------------------------------------------------------------------------------------


# import csv
# import logging
# import json
# from datetime import datetime
# from typing import Dict, List, Optional, Generator, Any
# from io import StringIO
# from emailflow.utils.database import insert_email, update_progress, insert_progress
# from emailflow.utils.helpers import clean_text, extract_email_addresses, extract_phone_numbers, parse_date, validate_csv_headers
# from emailflow.services.ai_service import ai_service
# from emailflow.models import Email, UploadProgress

# logger = logging.getLogger(__name__)

# from bson import ObjectId
# import uuid

# class EmailProcessor:
#     def __init__(self):
#         self.supported_encodings = ['utf-8', 'latin-1', 'cp1252']
    
#     def process_csv_file(self, file_path: str, filename: str) -> str:
#         """Process CSV file and return progress ID"""
#         progress_data = UploadProgress({
#             'filename': filename,
#             'total_rows': 0,
#             'processed_rows': 0,
#             'status': 'processing',
#             'error_message': ''
#         }).to_dict()
        
#         progress_id = insert_progress(progress_data)
        
#         try:
#             # First pass: count total rows
#             total_rows = self._count_csv_rows(file_path)
#             update_progress(progress_id, {'total_rows': total_rows})
            
#             # Second pass: process emails
#             self._process_csv_emails(file_path, progress_id)
            
#             # Mark as completed
#             update_progress(progress_id, {
#                 'status': 'completed',
#                 'updated_at': datetime.utcnow().isoformat()
#             })
            
#         except Exception as e:
#             logger.error(f"Error processing CSV file: {e}")
#             update_progress(progress_id, {
#                 'status': 'failed',
#                 'error_message': str(e),
#                 'updated_at': datetime.utcnow().isoformat()
#             })
        
#         return progress_id
    
#     def _count_csv_rows(self, file_path: str) -> int:
#         """Count total rows in CSV file"""
#         try:
#             for encoding in self.supported_encodings:
#                 try:
#                     with open(file_path, 'r', encoding=encoding) as file:
#                         csv_reader = csv.reader(file)
#                         try:
#                             next(csv_reader)  # Skip header
#                         except StopIteration:
#                             return 0  # Empty file
#                         return sum(1 for _ in csv_reader)
#                 except UnicodeDecodeError:
#                     continue
            
#             raise Exception("Unable to decode CSV file with supported encodings")
            
#         except Exception as e:
#             logger.error(f"Error counting CSV rows: {e}")
#             raise
    
#     def _process_csv_emails(self, file_path: str, progress_id: str):
#         """Process emails from CSV file"""
#         try:
#             error_count = 0
#             for encoding in self.supported_encodings:
#                 try:
#                     with open(file_path, 'r', encoding=encoding) as file:
#                         csv_reader = csv.DictReader(file)
#                         headers = csv_reader.fieldnames
                        
#                         # Validate headers
#                         if not headers:
#                             raise Exception("CSV file has no headers")
#                         header_mapping = validate_csv_headers(list(headers))
#                         if not all(key in header_mapping for key in ['sender', 'subject', 'body']):
#                             raise Exception("CSV must contain sender, subject, and body columns")
                        
#                         processed_count = 0
                        
#                         for row in csv_reader:
#                             try:
#                                 email_data = self._process_email_row(row, header_mapping)
#                                 insert_email(email_data)
                                
#                                 processed_count += 1
                                
#                                 # Update progress every 10 emails
#                                 if processed_count % 10 == 0:
#                                     update_progress(progress_id, {
#                                         'processed_rows': processed_count,
#                                         'error_count': error_count,
#                                         'updated_at': datetime.utcnow().isoformat()
#                                     })
                                
#                             except Exception as e:
#                                 logger.error(f"Error processing email row: {e}")
#                                 error_count += 1
#                                 continue
                        
#                         # Final progress update
#                         update_progress(progress_id, {
#                             'processed_rows': processed_count,
#                             'error_count': error_count,
#                             'updated_at': datetime.utcnow().isoformat()
#                         })
                        
#                         return
                        
#                 except UnicodeDecodeError:
#                     continue
            
#             raise Exception("Unable to decode CSV file with supported encodings")
            
#         except Exception as e:
#             logger.error(f"Error processing CSV emails: {e}")
#             raise
    
#     def _process_email_row(self, row: Dict[str, str], header_mapping: Dict[str, str]) -> Dict:
#         """Process individual email row"""
#         try:
#             # Extract basic fields
#             sender = clean_text(row.get(header_mapping['sender'], ''))
#             subject = clean_text(row.get(header_mapping['subject'], ''))
#             body = clean_text(row.get(header_mapping['body'], ''))
            
#             if not sender or not subject or not body:
#                 raise ValueError("Missing required fields: sender, subject, or body")
            
#             # Parse date
#             date_str = row.get(header_mapping.get('date', ''), '')
#             parsed_date = parse_date(date_str)
            
#             # AI Classification
#             classification_result = ai_service.classify_email(subject, body)
            
#             # Extract additional details
#             other_details = self._extract_details(body)
            
#             # Generate embeddings
#             embeddings_data = {}
#             text_for_embedding = f"{subject} {body}"
#             embeddings = ai_service.generate_embeddings([text_for_embedding])  # Pass as list
            
#             if embeddings:
#                 embeddings_data = {
#                     'vector': embeddings[0],  # Get first embedding
#                     'model': 'nvidia/nv-embedqa-e5-v5',
#                     'dim': len(embeddings[0])
#                 }
            
#             # Generate suggested responses
#             suggested_responses = []
#             response = ai_service.generate_response(subject, body, classification_result['classification'])
#             if response:
#                 suggested_responses.append(response)
            
#             # Create email document with unique _id
#             email_data = Email({
#                 'sender': sender,
#                 'email_subject': subject,
#                 'email_body': body,
#                 'priority': classification_result['priority'],
#                 'sentiment': classification_result['sentiment'],
#                 'classification': classification_result['classification'],
#                 'summary': classification_result['summary'],
#                 'filtered': False,  # TODO: Implement spam filtering
#                 'metadata': {
#                     'date': parsed_date.isoformat() if parsed_date else date_str,
#                     'date_epoch': int(parsed_date.timestamp()) if parsed_date else None,
#                     'original_row': dict(row)
#                 },
#                 'other_details': other_details,
#                 'suggested_responses': suggested_responses,
#                 'embeddings': embeddings_data,
#                 'created_at': datetime.utcnow().isoformat(),
#                 'updated_at': datetime.utcnow().isoformat()
#             }).to_dict()
            
#             # Ensure document has a unique _id
#             if '_id' not in email_data or email_data['_id'] is None:
#                 email_data['_id'] = ObjectId()
            
#             return email_data
            
#         except Exception as e:
#             logger.error(f"Error processing email row: {e}")
#             raise
    
#     def _extract_details(self, text: str) -> Dict[str, Any]:
#         """Extract additional details from email text"""
#         details = {}
        
#         # Extract email addresses
#         emails = extract_email_addresses(text)
#         if emails:
#             details['alternate_email'] = emails[0]  # Take first found email
        
#         # Extract phone numbers
#         phones = extract_phone_numbers(text)
#         if phones:
#             details['phone_number'] = phones[0]  # Take first found phone
        
#         # Extract potential addresses (simple pattern)
#         address_patterns = [
#             r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)',
#             r'[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}'
#         ]
        
#         import re
#         for pattern in address_patterns:
#             matches = re.findall(pattern, text, re.IGNORECASE)
#             if matches:
#                 details['address'] = matches[0]
#                 break
        
#         return details

# # Global email processor instance
# email_processor = EmailProcessor()







# import csv
# import logging
# from datetime import datetime
# from typing import Dict, Any
# import uuid
# from bson import ObjectId
# import re

# from emailflow.utils.database import insert_email, update_progress, insert_progress
# from emailflow.utils.helpers import clean_text, extract_email_addresses, extract_phone_numbers, parse_date, validate_csv_headers
# from emailflow.services.ai_service import ai_service
# from emailflow.models import Email, UploadProgress

# logger = logging.getLogger(__name__)

# class EmailProcessor:
#     def __init__(self):
#         self.supported_encodings = ['utf-8', 'latin-1', 'cp1252']
    
#     def process_csv_file(self, file_path: str, filename: str) -> str:
#         """Process CSV file and return progress ID"""
#         progress_data = UploadProgress({
#             'filename': filename,
#             'total_rows': 0,
#             'processed_rows': 0,
#             'status': 'processing',
#             'error_message': ''
#         }).to_dict()
        
#         progress_id = insert_progress(progress_data)
        
#         try:
#             # First pass: count total rows
#             total_rows = self._count_csv_rows(file_path)
#             update_progress(progress_id, {'total_rows': total_rows})
            
#             # Second pass: process emails
#             self._process_csv_emails(file_path, progress_id)
            
#             # Mark as completed
#             update_progress(progress_id, {
#                 'status': 'completed',
#                 'updated_at': datetime.utcnow().isoformat()
#             })
            
#         except Exception as e:
#             logger.error(f"Error processing CSV file: {e}")
#             update_progress(progress_id, {
#                 'status': 'failed',
#                 'error_message': str(e),
#                 'updated_at': datetime.utcnow().isoformat()
#             })
        
#         return progress_id
    
#     def _count_csv_rows(self, file_path: str) -> int:
#         """Count total rows in CSV file"""
#         try:
#             for encoding in self.supported_encodings:
#                 try:
#                     with open(file_path, 'r', encoding=encoding) as file:
#                         csv_reader = csv.reader(file)
#                         next(csv_reader)  # Skip header
#                         return sum(1 for _ in csv_reader)
#                 except UnicodeDecodeError:
#                     continue
            
#             raise Exception("Unable to decode CSV file with supported encodings")
            
#         except Exception as e:
#             logger.error(f"Error counting CSV rows: {e}")
#             raise
    
#     def _process_csv_emails(self, file_path: str, progress_id: str):
#         """Process emails from CSV file"""
#         try:
#             for encoding in self.supported_encodings:
#                 try:
#                     with open(file_path, 'r', encoding=encoding) as file:
#                         csv_reader = csv.DictReader(file)
#                         headers = csv_reader.fieldnames
                        
#                         # Validate headers
#                         if not headers:
#                             raise Exception("CSV file has no headers")
#                         header_mapping = validate_csv_headers(list(headers))
#                         if not all(key in header_mapping for key in ['sender', 'subject', 'body']):
#                             raise Exception("CSV must contain sender, subject, and body columns")
                        
#                         processed_count = 0
                        
#                         for row in csv_reader:
#                             try:
#                                 email_data = self._process_email_row(row, header_mapping)
#                                 insert_email(email_data)
                                
#                                 processed_count += 1
                                
#                                 # Update progress every 10 emails
#                                 if processed_count % 10 == 0:
#                                     update_progress(progress_id, {
#                                         'processed_rows': processed_count,
#                                         'updated_at': datetime.utcnow().isoformat()
#                                     })
                                
#                             except Exception as e:
#                                 logger.error(f"Error processing email row: {e}")
#                                 continue
                        
#                         # Final progress update
#                         update_progress(progress_id, {
#                             'processed_rows': processed_count,
#                             'updated_at': datetime.utcnow().isoformat()
#                         })
                        
#                         return
                        
#                 except UnicodeDecodeError:
#                     continue
            
#             raise Exception("Unable to decode CSV file with supported encodings")
            
#         except Exception as e:
#             logger.error(f"Error processing CSV emails: {e}")
#             raise
    
#     def _process_email_row(self, row: Dict[str, str], header_mapping: Dict[str, str]) -> Dict:
#         """Process individual email row"""
#         try:
#             # Extract basic fields
#             sender = clean_text(row.get(header_mapping['sender'], ''))
#             subject = clean_text(row.get(header_mapping['subject'], ''))
#             body = clean_text(row.get(header_mapping['body'], ''))
            
#             if not sender or not subject or not body:
#                 raise ValueError("Missing required fields: sender, subject, or body")
            
#             # Parse date
#             date_str = row.get(header_mapping.get('date', ''), '')
#             parsed_date = parse_date(date_str)
            
#             # AI Classification
#             classification_result = ai_service.classify_email(subject, body)
            
#             # Extract additional details
#             other_details = self._extract_details(body)
            
#             # Generate embeddings
#             embeddings_data = {}
#             text_for_embedding = f"{subject} {body}"
#             embeddings = ai_service.generate_embeddings([text_for_embedding])  # Pass as list
            
#             if embeddings:
#                 embeddings_data = {
#                     'vector': embeddings[0],  # Get first embedding
#                     'model': 'nvidia/nv-embedqa-e5-v5',
#                     'dim': len(embeddings[0])
#                 }
            
#             # Generate suggested responses
#             suggested_responses = []
#             response = ai_service.generate_response(subject, body, classification_result['classification'])
#             if response:
#                 suggested_responses.append(response)
            
#             # Create email document with unique _id
#             email_data = Email({
#                 'sender': sender,
#                 'email_subject': subject,
#                 'email_body': body,
#                 'priority': classification_result['priority'],
#                 'sentiment': classification_result['sentiment'],
#                 'classification': classification_result['classification'],
#                 'summary': classification_result['summary'],
#                 'filtered': False,  # TODO: Implement spam filtering
#                 'metadata': {
#                     'date': parsed_date.isoformat() if parsed_date else date_str,
#                     'date_epoch': int(parsed_date.timestamp()) if parsed_date else None,
#                     'original_row': dict(row)
#                 },
#                 'other_details': other_details,
#                 'suggested_responses': suggested_responses,
#                 'embeddings': embeddings_data,
#                 'created_at': datetime.utcnow().isoformat(),
#                 'updated_at': datetime.utcnow().isoformat()
#             }).to_dict()
            
#             return email_data
            
#         except Exception as e:
#             logger.error(f"Error processing email row: {e}")
#             raise
    
#     def _extract_details(self, text: str) -> Dict[str, Any]:
#         """Extract additional details from email text"""
#         details = {}
        
#         # Extract email addresses
#         emails = extract_email_addresses(text)
#         if emails:
#             details['alternate_email'] = emails[0]  # Take first found email
        
#         # Extract phone numbers
#         phones = extract_phone_numbers(text)
#         if phones:
#             details['phone_number'] = phones[0]  # Take first found phone
        
#         # Extract potential addresses (simple pattern)
#         address_patterns = [
#             r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)',
#             r'[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}'
#         ]
        
#         for pattern in address_patterns:
#             matches = re.findall(pattern, text, re.IGNORECASE)
#             if matches:
#                 details['address'] = matches[0]
#                 break
        
#         return details

# # Global email processor instance
# email_processor = EmailProcessor()










# services/email_processor.py (remove duplicated code and ensure embeddings work with new local method)
import csv
import logging
from datetime import datetime
from typing import Dict, Any
from bson import ObjectId
import re

from emailflow.utils.database import insert_email, update_progress, insert_progress
from emailflow.utils.helpers import clean_text, extract_email_addresses, extract_phone_numbers, parse_date, validate_csv_headers
from emailflow.services.ai_service import ai_service
from emailflow.models import Email, UploadProgress

logger = logging.getLogger(__name__)

class EmailProcessor:
    def __init__(self):
        self.supported_encodings = ['utf-8', 'latin-1', 'cp1252']
    
    def process_csv_file(self, file_path: str, filename: str) -> str:
        """Process CSV file and return progress ID"""
        progress_data = UploadProgress({
            'filename': filename,
            'total_rows': 0,
            'processed_rows': 0,
            'status': 'processing',
            'error_message': ''
        }).to_dict()
        
        progress_id = insert_progress(progress_data)
        
        try:
            # First pass: count total rows
            total_rows = self._count_csv_rows(file_path)
            update_progress(progress_id, {'total_rows': total_rows})
            
            # Second pass: process emails
            self._process_csv_emails(file_path, progress_id)
            
            # Mark as completed
            update_progress(progress_id, {
                'status': 'completed',
                'updated_at': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error processing CSV file: {e}")
            update_progress(progress_id, {
                'status': 'failed',
                'error_message': str(e),
                'updated_at': datetime.utcnow().isoformat()
            })
        
        return progress_id
    
    def _count_csv_rows(self, file_path: str) -> int:
        """Count total rows in CSV file"""
        try:
            for encoding in self.supported_encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        csv_reader = csv.reader(file)
                        next(csv_reader)  # Skip header
                        return sum(1 for _ in csv_reader)
                except UnicodeDecodeError:
                    continue
            
            raise Exception("Unable to decode CSV file with supported encodings")
            
        except Exception as e:
            logger.error(f"Error counting CSV rows: {e}")
            raise
    
    def _process_csv_emails(self, file_path: str, progress_id: str):
        """Process emails from CSV file"""
        try:
            for encoding in self.supported_encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        csv_reader = csv.DictReader(file)
                        headers = csv_reader.fieldnames
                        
                        # Validate headers
                        if not headers:
                            raise Exception("CSV file has no headers")
                        header_mapping = validate_csv_headers(list(headers))
                        if not all(key in header_mapping for key in ['sender', 'subject', 'body']):
                            raise Exception("CSV must contain sender, subject, and body columns")
                        
                        processed_count = 0
                        
                        for row in csv_reader:
                            try:
                                email_data = self._process_email_row(row, header_mapping)
                                insert_email(email_data)
                                
                                processed_count += 1
                                
                                # Update progress every 10 emails
                                if processed_count % 10 == 0:
                                    update_progress(progress_id, {
                                        'processed_rows': processed_count,
                                        'updated_at': datetime.utcnow().isoformat()
                                    })
                                
                            except Exception as e:
                                logger.error(f"Error processing email row: {e}")
                                continue
                        
                        # Final progress update
                        update_progress(progress_id, {
                            'processed_rows': processed_count,
                            'updated_at': datetime.utcnow().isoformat()
                        })
                        
                        return
                        
                except UnicodeDecodeError:
                    continue
            
            raise Exception("Unable to decode CSV file with supported encodings")
            
        except Exception as e:
            logger.error(f"Error processing CSV emails: {e}")
            raise
    
    def _process_email_row(self, row: Dict[str, str], header_mapping: Dict[str, str]) -> Dict:
        """Process individual email row"""
        try:
            # Extract basic fields
            sender = clean_text(row.get(header_mapping['sender'], ''))
            subject = clean_text(row.get(header_mapping['subject'], ''))
            body = clean_text(row.get(header_mapping['body'], ''))
            
            if not sender or not subject or not body:
                raise ValueError("Missing required fields: sender, subject, or body")
            
            # Parse date
            date_str = row.get(header_mapping.get('date', ''), '')
            parsed_date = parse_date(date_str)
            
            # AI Classification
            classification_result = ai_service.classify_email(subject, body)
            
            # Extract additional details
            other_details = self._extract_details(body)
            
            # Generate embeddings
            embeddings_data = {}
            text_for_embedding = f"{subject} {body}"
            embeddings = ai_service.generate_embeddings([text_for_embedding])  # Pass as list
            
            if embeddings:
                embeddings_data = {
                    'vector': embeddings[0],  # Get first embedding
                    'model': 'all-MiniLM-L6-v2',  # Update to local model name
                    'dim': len(embeddings[0])
                }
            
            # Generate suggested responses
            suggested_responses = []
            response = ai_service.generate_response(subject, body, classification_result['classification'])
            if response:
                suggested_responses.append(response)
            
            # Create email document with unique _id
            email_data = Email({
                'sender': sender,
                'email_subject': subject,
                'email_body': body,
                'priority': classification_result['priority'],
                'sentiment': classification_result['sentiment'],
                'classification': classification_result['classification'],
                'summary': classification_result['summary'],
                'filtered': False,  # TODO: Implement spam filtering
                'metadata': {
                    'date': parsed_date.isoformat() if parsed_date else date_str,
                    'date_epoch': int(parsed_date.timestamp()) if parsed_date else None,
                    'original_row': dict(row)
                },
                'other_details': other_details,
                'suggested_responses': suggested_responses,
                'embeddings': embeddings_data,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).to_dict()
            
            return email_data
            
        except Exception as e:
            logger.error(f"Error processing email row: {e}")
            raise
    
    def _extract_details(self, text: str) -> Dict[str, Any]:
        """Extract additional details from email text"""
        details = {}
        
        # Extract email addresses
        emails = extract_email_addresses(text)
        if emails:
            details['alternate_email'] = emails[0]  # Take first found email
        
        # Extract phone numbers
        phones = extract_phone_numbers(text)
        if phones:
            details['phone_number'] = phones[0]  # Take first found phone
        
        # Extract potential addresses (simple pattern)
        address_patterns = [
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)',
            r'[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}'
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                details['address'] = matches[0]
                break
        
        return details

# Global email processor instance
email_processor = EmailProcessor()