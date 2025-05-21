# Firebase Integration for Freya AI

This document explains how to use the simplified Firebase integration for the Freya AI chatbot. This integration provides a streamlined approach that uses Firebase/Firestore for data storage and retrieves memory context to enhance the chat experience.

## Overview

The Firebase integration provides:

1. A simplified REST API for chat interactions
2. Direct Firestore access for storing and retrieving data
3. Integration with the existing memory system
4. Authentication support via Firebase Authentication
5. Compatibility with the existing frontend

## Prerequisites

- Firebase project with Firestore database
- Firebase web app configuration
- (Optional) Firebase Admin SDK service account credentials

## Configuration

1. Copy the `.env.firebase` file to `.env`:
   ```bash
   cp .env.firebase .env
   ```

2. Update the `.env` file with your configuration:
   - Set your OpenAI API key
   - The Firebase configuration is already included, but you can update it if needed
   - (Optional) If you have a service account JSON file, specify its path or include it directly

## API Endpoints

The Firebase integration exposes the following endpoints:

### Chat Endpoint

```
POST /firebase/chat
```

Send a message and get a response with memory context.

**Request:**
```json
{
  "message": "Your message here",
  "user_id": "user123",
  "conversation_id": "optional_conversation_id",
  "include_memory": true
}
```

**Response:**
```json
{
  "message": "AI response message",
  "conversation_id": "conversation123",
  "message_id": "message456",
  "timestamp": "2025-05-21T12:34:56.789Z",
  "state_flags": {
    "listening": false,
    "thinking": false,
    "reply": true
  }
}
```

### Conversation Endpoints

```
GET /firebase/conversations/{user_id}
```
Get all conversations for a user.

```
GET /firebase/conversations/{conversation_id}/messages
```
Get all messages for a conversation.

```
DELETE /firebase/conversations/{conversation_id}
```
Delete a conversation.

### Memory Endpoints

```
GET /firebase/topics/{user_id}
```
Get all topics for a user.

```
GET /firebase/facts/{user_id}
```
Get all facts for a user.

## Authentication

The API supports Firebase Authentication. To authenticate requests:

1. Include an `Authorization` header with a Firebase ID token:
   ```
   Authorization: Bearer your_firebase_id_token
   ```

2. The user ID in the token must match the user ID in the request.

## Testing

To test the Firebase integration:

```bash
# Start the server
python -m uvicorn app.main:app --reload

# Run the test script
python scripts/test_firebase_chat.py
```

## Implementation Details

### Memory System

The Firebase integration maintains the same three-tier memory system:

1. **User Facts (Tier 1)**: Persistent facts about the user
2. **Recent History (Tier 2)**: Recent conversation context
3. **Topic Memory (Tier 3)**: Long-term topical memories

### Data Model

The Firestore data model mirrors the PostgreSQL schema:

- **Users Collection**: User information
- **Conversations Collection**: Conversation metadata
- **Messages Collection/Subcollection**: Message content
- **UserFacts Collection**: Extracted facts about users
- **Topics Collection**: Topic metadata

### Firebase Service

The `FirebaseService` class provides methods for:

- Connecting to Firebase
- Authenticating users
- CRUD operations for Firestore documents
- Retrieving memory context from Firestore

### Memory Service

The `FirebaseMemoryService` class provides methods for:

- Retrieving user facts
- Retrieving conversation history
- Retrieving topic memories
- Building comprehensive memory context

## Using with Frontend

To use the Firebase integration with the existing frontend:

1. Configure the frontend to use the `/firebase/chat` endpoint instead of the original endpoint
2. Use Firebase Authentication for user authentication
3. The state flags in the response match the existing frontend expectations

## Error Handling

The API returns standard HTTP error codes:

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid authentication token
- `403 Forbidden`: User doesn't have permission
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a detail message:

```json
{
  "detail": "Error message"
}
```

## Limitations

The current implementation has the following limitations:

1. No streaming support (uses standard request/response)
2. Simplified memory retrieval compared to the PostgreSQL implementation
3. Limited support for complex queries

## Next Steps

Potential enhancements:

1. Add streaming support using Firebase Realtime Database
2. Enhance memory retrieval with more sophisticated algorithms
3. Add support for more complex queries
4. Implement frontend compatibility layer