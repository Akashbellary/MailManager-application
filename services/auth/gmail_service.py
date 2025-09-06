import os
import logging
from typing import Dict, List, Optional, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
from datetime import datetime
from utils.database import insert_email, get_emails_collection
from models import Email

logger = logging.getLogger(__name__)

class GmailService:
    def __init__(self):
        self.client_id = "1053748567329-bt4mjg0m8tukuqt7qlbcn0sub6hlmceu.apps.googleusercontent.com"
        self.client_secret = "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"
        self.redirect_uri = "http://localhost:5000/auth/google-callback"  # Fixed URL with auth prefix
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
        self.credentials_file = 'gmail_credentials.json'
    
    def get_oauth_flow(self) -> Flow:
        """Create OAuth flow for Gmail authentication"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.scopes
        )
        flow.redirect_uri = self.redirect_uri
        return flow
    
    def authenticate_user(self) -> str:
        """Start OAuth flow and return authorization URL"""
        try:
            flow = self.get_oauth_flow()
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            return authorization_url
        except Exception as e:
            logger.error(f"Error creating authorization URL: {e}")
            raise
    
    def handle_callback(self, authorization_response: str) -> Dict[str, Any]:
        """Handle OAuth callback and store credentials"""
        try:
            flow = self.get_oauth_flow()
            flow.fetch_token(authorization_response=authorization_response)
            
            credentials = flow.credentials
            user_info = self.get_user_info(credentials)
            
            # Store credentials (in production, use secure storage)
            creds_data = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'user_email': user_info.get('email')
            }
            
            # Save credentials to file (in production, use database)
            with open(self.credentials_file, 'w') as f:
                json.dump(creds_data, f)
            
            return {
                'success': True,
                'user_info': user_info,
                'credentials': creds_data
            }
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_info(self, credentials: Credentials) -> Dict[str, Any]:
        """Get user info from Gmail API"""
        try:
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            return user_info
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return {}
    
    def get_gmail_service(self, user_email: str = None) -> Optional[Any]:
        """Get authenticated Gmail service"""
        try:
            # Load credentials
            if not os.path.exists(self.credentials_file):
                logger.warning("No credentials file found")
                return None
            
            with open(self.credentials_file, 'r') as f:
                creds_data = json.load(f)
            
            # Check if we're looking for a specific user
            if user_email and creds_data.get('user_email') != user_email:
                logger.warning(f"Credentials for {user_email} not found")
                return None
            
            # Create credentials object
            credentials = Credentials(
                token=creds_data['token'],
                refresh_token=creds_data.get('refresh_token'),
                token_uri=creds_data['token_uri'],
                client_id=creds_data['client_id'],
                client_secret=creds_data['client_secret'],
                scopes=creds_data['scopes']
            )
            
            # Refresh token if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                # Save refreshed credentials
                creds_data['token'] = credentials.token
                with open(self.credentials_file, 'w') as f:
                    json.dump(creds_data, f)
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=credentials)
            return service
            
        except Exception as e:
            logger.error(f"Error getting Gmail service: {e}")
            return None
    
    def fetch_emails(self, user_email: str = None, max_results: int = 100) -> List[Dict]:
        """Fetch emails from Gmail"""
        try:
            service = self.get_gmail_service(user_email)
            if not service:
                logger.warning("Unable to get Gmail service")
                return []
            
            # Fetch messages
            results = service.users().messages().list(
                userId='me',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                try:
                    msg = service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    # Parse email data
                    email_data = self._parse_email(msg)
                    if email_data:
                        emails.append(email_data)
                        
                except Exception as e:
                    logger.error(f"Error parsing message {message['id']}: {e}")
                    continue
            
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def _parse_email(self, message: Dict) -> Optional[Dict]:
        """Parse Gmail message into email data structure"""
        try:
            headers = message['payload'].get('headers', [])
            email_data = {
                'sender': '',
                'email_subject': '',
                'email_body': '',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'metadata': {
                    'gmail_id': message.get('id', ''),
                    'thread_id': message.get('threadId', ''),
                    'internal_date': message.get('internalDate', '')
                }
            }
            
            # Extract headers
            for header in headers:
                if header['name'] == 'From':
                    email_data['sender'] = header['value']
                elif header['name'] == 'Subject':
                    email_data['email_subject'] = header['value']
                elif header['name'] == 'Date':
                    email_data['metadata']['date'] = header['value']
            
            # Extract body
            email_data['email_body'] = self._extract_body(message)
            
            return email_data
            
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return None
    
    def _extract_body(self, message: Dict) -> str:
        """Extract email body from message"""
        try:
            payload = message['payload']
            body = ""
            
            if 'parts' in payload:
                # Handle multipart messages
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                        import base64
                        body_data = part['body']['data']
                        body += base64.urlsafe_b64decode(body_data).decode('utf-8')
                    elif part.get('mimeType') == 'text/html' and 'data' in part.get('body', {}) and not body:
                        # Fallback to HTML if no plain text
                        import base64
                        body_data = part['body']['data']
                        html_body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        # Simple HTML to text conversion
                        import re
                        body = re.sub('<[^<]+?>', '', html_body)
            elif 'body' in payload and 'data' in payload['body']:
                # Handle simple messages
                import base64
                body_data = payload['body']['data']
                body = base64.urlsafe_b64decode(body_data).decode('utf-8')
            
            return body
            
        except Exception as e:
            logger.error(f"Error extracting body: {e}")
            return ""
    
    def sync_emails_to_db(self, user_email: str = None, max_results: int = 100) -> Dict[str, Any]:
        """Sync Gmail emails to database"""
        try:
            # Fetch emails from Gmail
            gmail_emails = self.fetch_emails(user_email, max_results)
            
            if not gmail_emails:
                return {
                    'success': True,
                    'message': 'No emails fetched from Gmail',
                    'synced_count': 0
                }
            
            synced_count = 0
            skipped_count = 0
            
            # Sync to database
            for email_data in gmail_emails:
                try:
                    # Create Email object
                    email_obj = Email(email_data)
                    
                    # Check if email already exists
                    collection = get_emails_collection()
                    existing = collection.find_one({
                        'metadata.gmail_id': email_data['metadata']['gmail_id']
                    })
                    
                    if not existing:
                        # Insert new email
                        insert_email(email_obj.to_dict())
                        synced_count += 1
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    logger.error(f"Error syncing email to DB: {e}")
                    continue
            
            return {
                'success': True,
                'message': f'Synced {synced_count} new emails, skipped {skipped_count} existing',
                'synced_count': synced_count,
                'skipped_count': skipped_count
            }
            
        except Exception as e:
            logger.error(f"Error syncing emails to DB: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global Gmail service instance
gmail_service = GmailService()