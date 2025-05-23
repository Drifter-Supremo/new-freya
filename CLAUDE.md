# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

### Critical Rules - DO NOT VIOLATE

- **ALWAYS start every new task with reading the CLAUDE.md

- **NEVER create mock data or simplified components** unless explicitly told to do so

- **NEVER replace existing complex components with simplified versions** - always fix the actual problem

- **ALWAYS work with the existing codebase** - do not create new simplified alternatives

- **ALWAYS find and fix the root cause** of issues instead of creating workarounds

- When debugging issues, focus on fixing the existing implementation, not replacing it

- When something doesn't work, debug and fix it - don't start over with a simple version

- **ALWAYS check ALL /memory-bank DOCS before making changes** 

- NEVER complete multiple tasks in a row unless told to do so ALWAYS complete 1 task at a time then stop to regroup with me.

- ALWAYS update ALL relevant/memory-bank docs after every successful task

### Development Environment - IMPORTANT

- **Operating System**: macOS
- **Python**: Using native macOS Python (venv/bin/python)
- **Virtual Environment**: Located at `venv/` in project root
- **Database**: Firebase/Firestore (must have valid service account credentials)

### Quick Start Guide for Testing

1. **Activate Virtual Environment (macOS)**:
   ```bash
   cd "/Users/blackcanopy/Documents/Projects/new-freya-who-this"
   # Use macOS Python with virtual environment:
   source venv/bin/activate
   ```

2. **Start the FastAPI Server**:
   ```bash
   # Option 1: Using the helper script
   python scripts/run_server.py
   
   # Option 2: Direct uvicorn
   python -m uvicorn app.main:app --reload
   ```

3. **Run Tests**:
   ```bash
   # Run all tests
   python -m pytest tests/ -v
   
   # Run specific test file
   python -m pytest tests/test_conversation_endpoints.py -v
   
   # Run comprehensive integration tests
   python scripts/test_all.py
   ```

### Common Import Fixes

When imports fail, check these common issues:
1. `init_db` is in `app.core.init_db`, not `app.core.db`
2. User model has `username` field, not `name`
3. User model requires `hashed_password` field
4. All IDs are integers, not UUIDs

### Test Data Patterns

1. **Creating Test Users**:
   ```python
   from uuid import uuid4
   unique_id = uuid4().hex[:8]
   user_data = {
       "username": f"testuser_{unique_id}",  # NOT "name"
       "email": f"test_{unique_id}@example.com",
       "hashed_password": "dummy_password_hash"
   }
   ```

2. **Error Response Format**:
   - Errors return as `{"error": "message"}`, not `{"detail": "message"}`
   - Validation errors return as `{"error": "Validation error", "details": [...]}`

3. **Session Management in Tests**:
   - Always get IDs before using them: `user_id = test_user.id`
   - Use dependency injection for database sessions in tests

### Database Migrations

When adding new columns or database features:
```bash
# Create new migration
python -m alembic revision -m "description"

# Run migrations
python -m alembic upgrade head
```

### Firebase/Firestore Search

- Firestore collections: `userFacts`, `conversations`, `messages`
- Native Firestore querying and indexing
- Search functionality implemented in Firebase services

### TypeScript and Linting

- ALWAYS add explicit types to all function parameters, variables, and return types

- ALWAYS run npm build or whichever appropriate linter command before considering any code changes complete

- Fix all linter and TypeScript errors immediately - don't leave them for the user to fix

- When making changes to multiple files, check each one for type errors



### Web Access and MCP Tools

- Use the built-in WebFetch tool to access web content using the following syntax:
  ```
  WebFetch({
    url: "https://example.com/path",
    prompt: "Extract key information about [specific topic]"
  })
  ```

- The WebFetch tool can be used to:
  - Retrieve documentation
  - Research APIs and libraries
  - Access technical resources
  - View content from URLs the user provides

- If the user references specific URLs, always use WebFetch to retrieve and process the content

- Context7 MCP is available for vector storage and retrieval augmented generation:
  - This provides advanced RAG capabilities for knowledge management
  - Can be used for semantic search across documentation
  - Enables more context-aware responses based on stored information
  - Works well for persisting information across sessions

## Project Overview

Freya AI Companion is a fine-tuned GPT-4.1 Mini AI chatbot with a unique emotional persona and tiered memory system. The project consists of:

- **Backend**: Python 3.11+, FastAPI, Firebase/Firestore
- **Frontend**: React 18, Next.js 14, Tailwind CSS, shadcn/ui, Framer Motion  
- **AI Model**: Fine-tuned GPT-4.1 Mini: "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj"
- **Features**: Multi-tiered memory system (user facts, recent history, topics), OpenAI integration, Server-Sent Events (SSE)

## Common Development Commands

### Backend Commands (macOS)
```bash
# Path to project
cd "/Users/blackcanopy/Documents/Projects/new-freya-who-this"

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the backend
python -m uvicorn app.main:app --reload
# Or use the helper script:
python scripts/run_server.py

# Firebase testing
python scripts/test_firebase_connection.py  # Test Firebase connectivity
python scripts/test_firebase_chat.py        # Test Firebase chat API

# Testing
python scripts/test_event_dispatcher.py     # Test SSE events
python scripts/test_sse_endpoint.py         # Test SSE streaming
```

### Quick Testing Workflow
```bash
# Terminal 1: Start the server
cd "/Users/blackcanopy/Documents/Projects/new-freya-who-this"
source venv/bin/activate
python scripts/run_server.py

# Terminal 2: Run Firebase tests
cd "/Users/blackcanopy/Documents/Projects/new-freya-who-this"
source venv/bin/activate
python scripts/test_firebase_connection.py  # Basic connectivity
python scripts/test_firebase_chat.py        # Full chat API
```

### Testing Server-Sent Events (SSE)
```bash
# Terminal 1: Start the server
cd "/Users/blackcanopy/Documents/Projects/new-freya-who-this"
source venv/bin/activate
python scripts/run_server.py

# Terminal 2: Test SSE endpoint
cd "/Users/blackcanopy/Documents/Projects/new-freya-who-this"
source venv/bin/activate
python scripts/test_sse_endpoint.py     # Basic SSE test
python scripts/test_event_dispatcher.py # Event dispatcher test
python scripts/test_sse_raw.py         # Detailed event inspection
```

### Frontend Commands
```bash
cd freya-ui
npm install                      # Install dependencies
npm run dev                      # Run development server
npm run build                    # Build for production
npm run lint                     # Run linter
```

### Code Quality
```bash
black app/                       # Format Python code
isort app/                       # Sort imports
flake8 app/                      # Lint Python code
```

## High-Level Architecture

### Memory System (Three Tiers)
1. **User Facts (Tier 1)**: Persistent facts about the user stored with regex pattern matching
   - Implementation: `app/core/user_fact_service.py`, `utils/fact_patterns.py`
   - Test coverage: `tests/test_fact_patterns.py`

2. **Recent History (Tier 2)**: Recent conversation context
   - Implementation: `app/core/conversation_history_service.py`
   - Repository: `app/repository/conversation.py`

3. **Topic Memory (Tier 3)**: Long-term topical memories using Firestore queries
   - Topic extraction: `app/services/topic_extraction.py`
   - Tagging service: `app/services/topic_tagging.py`
   - Search implementation: `app/services/topic_search.py`
   - Memory service: `app/services/topic_memory_service.py`

### Memory Context Builder
The core memory system is orchestrated by `app/core/memory_context_service.py` which:
- Detects memory-related queries
- Extracts topics from user queries
- Prioritizes memories based on relevance
- Formats memory context for GPT-4.1 Mini

### OpenAI Integration
- Service wrapper: `app/services/openai_service.py`
- Uses fine-tuned model with parameters:
  - temperature: 1
  - max_tokens: 800
- System prompt defined in `memory-bank/tasks.md` (lines 244-283)

### Frontend Integration
The backend communicates with the React frontend via browser events:
- `freya:listening`: When Freya starts listening
- `freya:thinking`: When processing
- `freya:reply`: When sending response

### Firebase/Firestore Schema
Collections in Firestore:
- `userFacts`: User fact storage with fields `timestamp`, `type`, `value`
- `conversations`: Conversation tracking with `userId`, `createdAt`, `updatedAt`
- `messages`: Message storage with `timestamp`, `user` (content field)

Uses Firestore's native querying and indexing capabilities.

### API Structure
Routes organized in `app/api/routes/`:
- `/health`: Basic health check
- `/events`: Server-Sent Events for real-time communication
- `/firebase`: Firebase integration endpoints
  - `/firebase/chat`: Main chat API with memory integration
  - `/firebase/conversations/{user_id}`: Get user conversations
  - `/firebase/facts/{user_id}`: Get user facts
  - `/firebase/topics/{user_id}`: Get user topics

### Testing Strategy
- Firebase connectivity tests with real production data
- Integration tests for Firebase/Firestore services
- Server-Sent Events (SSE) testing for real-time communication
- OpenAI integration tests with memory context
- Production Firestore database used for testing
- Unit tests run without pytest dependency for simplicity
- Test files:
  - `scripts/test_firebase_chat.py` - Full integration tests with real API calls
  - `scripts/test_firebase_unit.py` - Simple unit tests (4 tests, all passing)
  - `tests/test_firebase_integration.py` - Comprehensive unit tests using unittest

### Environment Configuration
Required environment variables (see `.env.example`):
- `OPENAI_API_KEY`: OpenAI API access
- `LOG_LEVEL`: Optional logging configuration

Firebase configuration is handled via service account credentials file.

### Firebase Integration (Phase 5 - Completed)
The project uses Firebase/Firestore as the primary backend:
- **Firebase Service**: `app/services/firebase_service.py` - Complete Firestore integration
- **Firebase Memory Service**: `app/services/firebase_memory_service.py` - Memory retrieval from Firestore
- **Firebase Chat API**: `app/api/routes/firebase_chat.py` - Simplified chat endpoint
- **Configuration**: `app/core/firebase_config.py` - Firebase project settings
- **Service Account**: Uses `freya-ai-chat-firebase-adminsdk-fbsvc-0af7f65b8e.json` for authentication (not included in repository for security)

**Firebase Testing**:
```bash
# Test Firebase connectivity and data retrieval
python scripts/test_firebase_connection.py

# Test complete Firebase chat API
python scripts/test_firebase_chat.py
```

**Firestore Collections**:
- `userFacts`: User facts with fields `timestamp`, `type`, `value`
- `conversations`: Conversation metadata with `userId`, `createdAt`, `updatedAt`
- `messages`: Message content with `timestamp`, `user` (content field)

### Key Implementation Notes
1. **Firebase/Firestore Backend**: The app uses Firebase/Firestore as the primary database backend
2. **Firebase Integration**: Successfully tested with production Firestore data and user facts
3. **Memory prioritization**: Implemented scoring algorithms for relevance-based memory retrieval from Firestore
4. **Real-time Communication**: Server-Sent Events (SSE) for browser integration
5. **Error handling**: Centralized error handling in `app/core/errors.py`
6. **Logging**: Configured via `app/core/config.py` 
7. **CORS**: Development configuration allows all origins

### Progress Tracking
Detailed task breakdown in `memory-bank/tasks.md` tracks implementation phases:
- Phase 1-3: ✅ Completed (Setup, Database, Memory System)
- Phase 4: ✅ Completed (OpenAI Integration & API Endpoints)
  - OpenAI service integration with fine-tuned GPT-4.1 Mini model
  - Memory context injection working with Firestore data
  - Firebase chat API endpoints implemented
  - All integration tests passing
- Phase 5: ✅ Completed (Simplified Firebase Integration) [2025-05-21]
  - ✅ Server-Sent Events (SSE) endpoint implemented and tested
  - ✅ EventService for event formatting and connection handling created
  - ✅ Firebase Admin SDK integration with existing Firestore database
  - ✅ Firebase memory service working with real user data (11 user facts)
  - ✅ Simplified Firebase chat API fully functional
  - ✅ All integration tests passing with production Firestore data
  - ✅ Frontend compatibility verified with real API calls
  - Real-time streamed responses from OpenAI working successfully
  - Fine-tuned GPT-4.1 Mini responding with personalized memory context
- Phase 6: ✅ Completed - Testing & Refinement [Started 2025-05-22, Completed 2025-05-23]
  - ✅ Unit tests for Firebase integration (4/4 tests passing)
  - ✅ Memory retrieval functionality tests (10/10 tests passing)
  - ✅ Chat endpoint integration tests (all tests passing)
  - ✅ OpenAI integration tests (9/9 tests passing)
  - ✅ Frontend end-to-end tests (6/6 UI compatibility tests passing)
  - ✅ Firestore query optimization completed with 50-64% performance improvements
  - ✅ Migration executed successfully: 11 userFacts + 253 messages updated
  - ✅ Caching implementation achieving 65,000x speedup on cache hits
- Error Handling & Logging: ✅ Completed [2025-05-23]
  - ✅ Robust error handling with global handlers and consistent JSON format
  - ✅ Structured logging across all services with proper levels and stack traces
  - ✅ User-friendly error messages with security-conscious messaging
  - ✅ Critical error monitoring with 58 logging instances and health check endpoint
- Phase 7-8: Deployment (pending)

### Recent Achievements 

#### Error Handling & Logging - COMPLETED [2025-05-23]
- Successfully implemented comprehensive error handling and logging across the entire application
- **Robust Error Handling**: Global error handlers with consistent JSON format, comprehensive API route error handling
- **Structured Logging**: Centralized configuration with 58 error logging instances across all services
- **User-Friendly Error Messages**: Clear, descriptive messages with proper HTTP status codes and validation details
- **Critical Error Monitoring**: Health check endpoint, full stack traces, and production-ready monitoring
- All error handling scenarios tested and verified (6/6 UI compatibility tests passing)

#### Phase 6 (Testing & Refinement) - COMPLETED [2025-05-23]
- Successfully created comprehensive testing suite covering all major functionality
- Created unit tests: `tests/test_firebase_integration.py` and `scripts/test_firebase_unit.py` (4/4 passing)
- Memory retrieval tests: `scripts/test_memory_retrieval.py` (10/10 passing with 94.4% accuracy)
- Chat endpoint tests: All integration tests passing with real Firebase data
- OpenAI integration tests: `scripts/test_openai_integration.py` (9/9 passing with streaming)
- UI compatibility tests: `scripts/test_ui_compatibility.py` (6/6 passing)
- **FIRESTORE OPTIMIZATION COMPLETED**: 50-64% query performance improvements, 65,000x cache speedups
- **SUCCESSFUL MIGRATION**: Updated 11 userFacts + 253 messages with userId/conversationId/topicIds fields
- Created comprehensive optimization documentation and validation tools

#### Phase 5 (Simplified Firebase Integration) - Completed [2025-05-21]
- Successfully implemented complete Firebase/Firestore integration with production data
- Created Firebase services for memory retrieval and chat API functionality
- Successfully connected to existing Firestore database and retrieved real user data
- Implemented memory-aware chat responses using actual user facts from Firestore
- All Firebase integration tests passing with real production data
- Fine-tuned GPT-4.1 Mini responding with personalized context from Firestore
- Firebase/Firestore backend architecture fully functional

#### Phase 5 (SSE Frontend Integration) - Completed [2025-05-19]
- Successfully implemented Server-Sent Events (SSE) endpoints for real-time communication
- Created `/events/stream` for establishing SSE connections and `/events/chat` for streaming responses
- Implemented EventService for proper event formatting and delivery
- Created multiple test scripts to verify functionality
- Demonstrated successful end-to-end testing with real OpenAI API calls and streamed responses
- Fixed virtual environment issues and provided reliable startup commands for macOS

#### Phase 4 (OpenAI Integration) - Completed [2025-05-19]
- Successfully implemented the `/chat/completions` endpoint with full memory context integration
- Fixed database schema issues (added `role` column to messages via Alembic migration)
- Updated all models and repositories to match proper field names
- Created comprehensive test suite with 100% pass rate:
  - Health endpoint test ✅
  - User creation test ✅
  - Basic chat completion test ✅
  - Memory query test ✅
  - Error handling tests ✅
- Created helper scripts for easier development and testing
- **Completed all conversation management endpoints**: 
  - POST `/conversations/` - Create new conversation
  - Firebase chat and memory endpoints with Firestore integration
  - DELETE `/conversations/{conversation_id}` - Delete with authorization
  - Fixed all existing endpoints for proper functioning
- **Added database migration** for tsvector trigger to support full-text search
- **All Phase 4 tests passing** - 11/11 conversation endpoint tests successful

### Troubleshooting Common Issues

1. **Virtual environment activation issues**:
   - Use `source venv/bin/activate` on macOS
   - Ensure Python 3.11+ is installed on your system

2. **Import errors with test files**:
   - Delete `__pycache__` directories if tests have same names as scripts
   - Use unique names for test files vs script files

3. **Firebase connection issues**:
   - Ensure Firebase service account credentials file exists
   - Verify Firestore collections are set up correctly
   - Check Firebase project configuration

4. **Firebase authentication issues**:
   - Verify service account file permissions
   - Check Firebase project ID in configuration
   - Ensure Firestore is enabled for your Firebase project

5. **Memory retrieval not working**:
   - Test Firebase connectivity: `python scripts/test_firebase_connection.py`
   - Verify user facts exist in Firestore
   - Check Firestore security rules

### Quick Reference - Key Patterns

```python
# Correct user creation
user_data = {
    "username": "testuser",    # NOT "name"
    "email": "test@example.com",
    "hashed_password": "dummy"  # Required field
}

# Error handling in API
try:
    # code
except HTTPException as e:
    return {"error": e.detail}  # NOT {"detail": e.detail}

# Test fixture session override
app.dependency_overrides[get_db] = override_get_db
```