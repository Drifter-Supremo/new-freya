# System Patterns: Freya Backend

> **Database Testing Policy**: All database operations and tests must be run against a PostgreSQL database. SQLite is not supported due to the use of PostgreSQL-specific features such as:
> - Full-text search (`TSVECTOR/TSQUERY`)
> - JSONB data type and operations
> - Advanced indexing features
> - Specific SQL functions and syntax
>
> Test configurations must connect to a PostgreSQL database instance that matches the production database version.

## System Architecture

- Modular FastAPI structure: entrypoint (`main.py`) is minimal and only wires together routers, error handlers, and config; all configuration and error handling is in `core/`, all API endpoints are in `api/routes/`. No file should exceed 300-400 lines; everything is organized for maintainability.
- Health (`/health`) and db-health (`/db-health`) endpoints for application and database monitoring.
- Connection pooling for PostgreSQL using SQLAlchemy's QueuePool.
- Alembic is used for schema versioning and migrations, with an alembic_version table in the DB to track schema state.
- All schema changes are made via versioned migration scripts, decoupling model changes from app runtime.

- Database initialization script for automated table creation.
- Dedicated endpoint for live database connection testing.
- Stateless REST API using FastAPI (Python).
- PostgreSQL as the primary data store, replacing Firebase.
- Three-tier memory architecture:
  1. User Facts
  2. Recent History
  3. Topic Memory
- Memory context assembly engine injects relevant memory into each API call.
- Event-driven communication with frontend via custom browser events.

## Key Technical Decisions

- Use FastAPI for high performance and async support.
- SQLModel or SQLAlchemy for ORM and migrations (with Alembic).
- Structured logging and validation for all endpoints.
- Full-text search enabled in PostgreSQL for topic retrieval.
- Migration tooling for Firestore → PostgreSQL data transfer.

## Design Patterns

- **Repository Query Pattern**: Dedicated repository for efficient user/topic/fact/message retrieval using SQLAlchemy joins and eager loading. All datetime fields use timezone-aware UTC datetimes for future compatibility.
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
  - `TopicExtractor` identifies potential topics from message content
  - `TopicTaggingService` persists topics and their relationships
  - Other services handle different aspects of the memory system
- **Data Access Layer**:
  - Repository pattern for database operations
  - SQLAlchemy ORM for database interactions
  - PostgreSQL-specific features (TSVECTOR, JSONB) for optimized queries
- **Memory System**:
  - Three-tier architecture (User Facts, Recent History, Topic Memory)
  - Memory context engine aggregates data from all tiers
- **Frontend Integration**:
  - Communicates with backend via browser events and REST endpoints
  - Custom events for real-time updates
- **Infrastructure**:
  - Centralized logging and error handling
  - Configuration management via environment variables

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
- Unit tests: Basic functionality testing
- Integration tests: End-to-end flow validation
- Helper scripts: Manual testing and debugging
- All tests must run against PostgreSQL (not SQLite)
