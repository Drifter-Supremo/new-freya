# System Patterns: Freya Backend

> **Database Testing Policy**: All database operations and tests are run against Firebase/Firestore. The application follows the simplified approach and uses the existing production Firestore database. No PostgreSQL or SQL-based testing is required.

## System Architecture

- Modular FastAPI structure: entrypoint (`main.py`) is minimal and only wires together routers, error handlers, and config; all configuration and error handling is in `core/`, all API endpoints are in `api/routes/`. No file should exceed 300-400 lines; everything is organized for maintainability.
- Health (`/health`) endpoint for application monitoring.
- Firebase/Firestore as the primary data store (no PostgreSQL).
- No database migrations needed - using existing Firestore schema.
- Simple, stateless REST API using FastAPI (Python).
- Three-tier memory architecture:
  1. User Facts (stored in Firestore)
  2. Recent History (retrieved from Firestore)
  3. Topic Memory (queried from Firestore)
- Memory context assembly engine injects relevant memory into each API call.
- Event-driven communication with frontend via custom browser events.
- Server-Sent Events (SSE) for real-time communication.

## Key Technical Decisions

- Use FastAPI for high performance and async support.
- Firebase Admin SDK for Firestore operations.
- Structured logging and validation for all endpoints.
- Native Firestore querying for topic retrieval.
- No migration needed - using existing Firestore database.
- Follow simplified approach - avoid unnecessary complexity.

## Design Patterns

- **Service Pattern**: Firebase services handle all Firestore operations. Memory services aggregate data from multiple collections.
- **Service Layer**: Business logic and memory context assembly are handled in dedicated service classes.
  - `TopicExtractor` service for extracting and scoring topics from messages
  - `TopicTaggingService` for managing topic persistence and message-topic associations
  - `OpenAIService` for handling API interactions with OpenAI
- **Retry and Backoff Pattern**: Implemented in `OpenAIService` for handling rate limits and temporary API failures with exponential backoff.
- **DTOs (Data Transfer Objects)**: Used for API request/response validation.
- **Error Handling Middleware**: Provides consistent fallback behavior.
- **Pattern Matching**:
  - Regex patterns for user fact extraction in `utils/fact_patterns.py` with tests in `tests/test_fact_patterns.py`
  - Keyword-based topic extraction in `app/services/topic_extraction.py` with tests in `tests/test_topic_extraction.py`

## Component Relationships

### Chat Completion Flow

#### Chat Endpoint
- **Location**: `app/api/routes/chat.py`
- **Responsibility**: Handles chat completion requests
- **Key Patterns**:
  - Uses integer IDs for users and conversations (not UUIDs)
  - Validates requests using Pydantic V2 field validators
  - Integrates memory context before calling OpenAI
  - Manages conversation lifecycle (create/continue)
  - Stores both user and assistant messages

#### Integration Points
1. **Request Flow**:
   - Client → FastAPI → Chat Endpoint → Services → Database
   - Memory Context Builder assembles context
   - OpenAI Service makes API call
   - Response formatted and returned

2. **Error Handling**:
   - Custom error handler for JSON serialization
   - Proper HTTP status codes (404, 422, 500)
   - Detailed error messages for debugging

### OpenAI Integration Components

#### OpenAIService
- **Location**: `app/services/openai_service.py`
- **Responsibility**: Handles all interactions with the OpenAI API
- **Features**:
  - Manages API authentication and request formatting
  - Implements retry logic with exponential backoff
  - Supports both streaming and non-streaming responses
  - Provides system prompt formatting with memory context
  - Includes specialized methods for Freya's chat completions

#### OpenAI Constants
- **Location**: `app/core/openai_constants.py`
- **Responsibility**: Centralizes OpenAI configuration values
- **Features**:
  - Default model specification (fine-tuned GPT-4.1 mini)
  - Temperature and token settings
  - Retry configuration
  - Freya's system prompt

### Topic Memory Components

#### TopicExtractor Service
- **Location**: `app/services/topic_extraction.py`
- **Responsibility**: Analyzes message content to identify relevant topics
- **Features**:
  - Keyword-based topic matching across 15+ categories
  - Case-insensitive whole-word matching with word boundaries
  - Relevance scoring for matched topics
  - Configurable topic categories and keywords

#### TopicTaggingService
- **Location**: `app/services/topic_tagging.py`
- **Responsibility**: Manages topic persistence and message-topic associations
- **Features**:
  - Creates and retrieves topics from the database
  - Associates messages with topics in a many-to-many relationship
  - Prevents duplicate topics with case-insensitive matching
  - Efficient transaction management for database operations

### System Integration

- **API Layer**: Endpoints in `api/routes/` handle HTTP requests and responses
- **Service Layer**:
  - `FirebaseService` handles all Firestore operations
  - `FirebaseMemoryService` retrieves and assembles memory context
  - `TopicExtractor` identifies potential topics from message content
  - `OpenAIService` handles chat completions with memory context
- **Data Access Layer**:
  - Firebase Admin SDK for Firestore operations
  - Native Firestore querying and filtering
  - No ORM needed - direct document operations
- **Memory System**:
  - Three-tier architecture (User Facts, Recent History, Topic Memory)
  - All tiers stored in Firestore collections
  - Memory context engine aggregates data from all tiers
- **Frontend Integration**:
  - Communicates via REST API and Server-Sent Events
  - Legacy compatibility with window.sendMessageToAPI
  - Custom events for real-time updates
- **Infrastructure**:
  - Centralized logging and error handling
  - Configuration management via environment variables
  - Firebase credentials managed securely

## Testing Patterns

### Integration Testing
- **Script**: `scripts/test_all.py`
- **Approach**: 
  - Starts server in background process
  - Runs comprehensive test suite
  - Tests actual API calls and database interactions
  - Validates end-to-end functionality

### Test Helpers
- **User Creation**: `scripts/create_test_user.py` - Creates test users with unique IDs
- **Server Runner**: `scripts/run_server.py` - Quick server startup script
- **Simple Tests**: `scripts/test_chat_simple.py` - Direct endpoint testing

### Test Coverage
- Unit tests: Basic functionality testing without pytest dependency
- Integration tests: End-to-end flow validation with real API calls
- Helper scripts: Manual testing and debugging
- All tests run against Firebase/Firestore production data
- Test files:
  - `scripts/test_firebase_unit.py` - Simple unit tests (4 tests passing)
  - `scripts/test_firebase_chat.py` - Full integration tests
  - `tests/test_firebase_integration.py` - Comprehensive unit tests
