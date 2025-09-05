# Overview

Email Triage AI is a Flask-based web application that automates email classification and response generation using AI. The system processes CSV uploads of emails, analyzes them using NVIDIA's AI models to classify priority, sentiment, and content categories, generates suggested responses, and provides an approval workflow for response management. The application features a dashboard with analytics, advanced search capabilities including natural language queries, and comprehensive email management tools.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 for responsive UI
- **JavaScript Framework**: Vanilla JavaScript with modular component initialization
- **CSS Framework**: Bootstrap 5 with custom CSS for enhanced styling
- **Client-side Features**: Form validation, file upload progress tracking, search functionality, and keyboard shortcuts

## Backend Architecture
- **Web Framework**: Flask with Blueprint-based modular routing structure
- **Route Organization**: Separate blueprints for dashboard, emails, approval queue, and search functionality
- **File Processing**: Asynchronous CSV processing with progress tracking
- **Session Management**: Flask sessions with configurable secret keys
- **Error Handling**: Comprehensive error handlers for 404, 500, and file size limit errors

## Data Models
- **Email Model**: Stores email content, AI-generated classifications (priority, sentiment, category), suggested responses, and metadata
- **Response Model**: Manages draft responses with approval workflow states (pending, approved, sent, rejected)
- **Progress Model**: Tracks CSV upload and processing status with real-time updates

## AI Integration
- **NVIDIA API Client**: Integration with NVIDIA's AI models for text classification and embeddings
- **Classification Pipeline**: Automated analysis of emails for priority (High/Medium/Low), sentiment (Positive/Neutral/Negative), and classification (Support/Query/Request/Help)
- **Response Generation**: AI-powered draft response creation with suggested responses
- **Semantic Search**: Vector embeddings for natural language search capabilities

## Search and Filtering
- **Natural Language Search**: AI-powered query interpretation with filter extraction
- **Vector Search**: Semantic similarity search using embeddings
- **Advanced Filtering**: Multi-criteria filtering by priority, sentiment, classification, sender, and date ranges
- **Search Service**: Unified search interface supporting both semantic and filter-based queries

## Approval Workflow
- **Draft Management**: System for creating, reviewing, and approving AI-generated responses
- **Status Tracking**: Multi-state workflow (pending → approved → sent)
- **Approval Queue**: Dedicated interface for reviewing and managing pending responses
- **Audit Trail**: Tracking of approval actions and timestamps

# External Dependencies

## AI Services
- **NVIDIA AI Platform**: Primary AI service for text classification, response generation, and embeddings via OpenAI-compatible API
- **Model Integration**: Uses NVIDIA's embedding models (nv-embedqa-e5-v5) and chat completion models

## Database
- **MongoDB**: Primary database for storing emails, responses, and progress tracking
- **PyMongo**: MongoDB Python driver for database operations
- **Connection Management**: Configurable MongoDB URI with connection pooling

## Third-party Libraries
- **Flask**: Core web framework with Werkzeug middleware
- **Bootstrap 5**: Frontend CSS framework for responsive design
- **Font Awesome**: Icon library for UI components
- **Chart.js**: JavaScript charting library for dashboard analytics
- **OpenAI Python Client**: Used to interface with NVIDIA's OpenAI-compatible API

## Development Tools
- **CSV Processing**: Built-in Python CSV module for file parsing
- **Date Handling**: python-dateutil for flexible date parsing
- **Text Processing**: Regular expressions for email and phone number extraction
- **File Handling**: Werkzeug utilities for secure file uploads

## Configuration Requirements
- **Environment Variables**: NVIDIA_API_KEY for AI services, MONGODB_URI for database connection, SESSION_SECRET for security
- **File Upload**: Configurable upload folder with size limits (100MB default)
- **Logging**: Structured logging with configurable levels for debugging and monitoring