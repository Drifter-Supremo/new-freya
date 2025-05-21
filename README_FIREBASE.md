# Freya AI Companion - Firebase Integration

This README explains the Firebase-based implementation for Freya AI Companion, which uses the existing Firestore database as the primary backend.

## Overview

The Firebase approach:

1. Uses Firebase/Firestore for data storage
2. Provides both REST API and Server-Sent Events (SSE) for real-time communication
3. Maintains compatibility with the existing frontend
4. Preserves the 3-tier memory system (user facts, recent history, topics)
5. Successfully tested with production Firestore data

## Getting Started

### Prerequisites

- Python 3.11+
- Firebase project with Firestore database
- OpenAI API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/new-freya-who-this.git
   cd new-freya-who-this
   ```

2. Create and activate a virtual environment:
   ```bash
   # On macOS
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.firebase .env
   # Edit .env with your configuration
   ```

### Running the Server

```bash
# Start the server
python -m uvicorn app.main:app --reload
```

The server will start at http://localhost:8000 with the Firebase integration available at `/firebase` endpoints.

### Testing

```bash
# Run the Firebase integration tests
python scripts/test_firebase_chat.py
```

## API Endpoints

### Chat API

- `POST /firebase/chat` - Send a message and get a response

### Conversation Management

- `GET /firebase/conversations/{user_id}` - Get user conversations
- `GET /firebase/conversations/{conversation_id}/messages` - Get conversation messages
- `DELETE /firebase/conversations/{conversation_id}` - Delete a conversation

### Memory Access

- `GET /firebase/topics/{user_id}` - Get user topics
- `GET /firebase/facts/{user_id}` - Get user facts

## Firebase Integration

The Firebase integration consists of:

1. **FirebaseService** (`app/services/firebase_service.py`) - Core service for Firestore access
2. **FirebaseMemoryService** (`app/services/firebase_memory_service.py`) - Memory context retrieval
3. **Firebase API Routes** (`app/api/routes/firebase_chat.py`) - REST API endpoints

## Configuration

Firebase configuration is stored in `.env.firebase`:
- Firebase web app configuration
- OpenAI API key
- (Optional) Firebase service account path

## Memory System

The Freya memory system has three tiers:

1. **User Facts (Tier 1)** - Persistent facts about the user
2. **Recent History (Tier 2)** - Recent conversation context
3. **Topic Memory (Tier 3)** - Long-term topical memories

All three tiers are implemented through Firestore collections.

## Frontend Integration

To use with the existing frontend:
1. Configure to use the `/firebase/chat` endpoint
2. Use the response state flags for UI state
3. No need for SSE/streaming events

## Authentication

The API supports Firebase Authentication:
- Include an `Authorization` header with a Firebase ID token
- The user ID in the token must match the user ID in requests

## Documentation

For more detailed documentation, see:
- `docs/firebase_integration.md` - Detailed Firebase integration
- `app/services/firebase_service.py` - Core Firebase service
- `scripts/test_firebase_chat.py` - Usage examples

## Troubleshooting

### Import Errors

If you encounter import errors related to Firebase:
```bash
pip install firebase-admin google-cloud-firestore
```

### Authentication Issues

If you have authentication issues:
- Check your Firebase project settings
- Verify the Firebase configuration in `.env`
- Ensure you have the correct permissions

### Database Access

If you have Firestore access issues:
- Check your Firebase security rules
- Verify service account credentials if used
- Ensure your project ID is correct

## Support

For issues or questions, please open an issue on GitHub.