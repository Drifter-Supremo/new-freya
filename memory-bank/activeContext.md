# Active Context: Freya Backend Rebuild

> **Testing Requirements**: All database tests must be run against PostgreSQL (not SQLite). The application uses PostgreSQL-specific features including full-text search (`TSVECTOR`), JSONB fields, and other PostgreSQL-specific optimizations. Test configurations should connect to a PostgreSQL database with the same version as production.

> Backend setup phase complete—modular FastAPI structure, health and db-health endpoints, PostgreSQL pooling, DB initialization script, and connection testing endpoint all working. Developer experience is smooth and maintainable compared to Node.js.
- Database schema and all core models fully implemented and tested.
- Alembic set up for migrations, initial migration script created and applied to PostgreSQL, schema versioning in place.
- Ready to begin database access layer (repository pattern, CRUD, etc).
> Modular refactor complete; backend code is now split into core/ (config, errors), api/routes/ (endpoints), and main.py (entrypoint only). No file will exceed 300-400 lines. Server and health endpoint work after refactor.

## Tier 3: Topic Memory Implementation

### Topic Extraction
- Implemented `TopicExtractor` service in `app/services/topic_extraction.py`
  - Ported from legacy JavaScript with significant enhancements
  - Supports 15+ topic categories with keyword-based matching
  - Case-insensitive whole-word matching with word boundaries
  - Scoring system to rank topics by relevance
  - 100% test coverage in `tests/test_topic_extraction.py`
  - Example usage in `examples/topic_extraction_demo.py`

### Topic Tagging Service
- Implemented `TopicTaggingService` in `app/services/topic_tagging.py`
  - Handles all database operations for topics and message-topic associations
  - Methods for tagging messages and retrieving message topics
  - Prevents duplicate topics with case-insensitive matching
  - Efficient transaction management for database operations
  - Comprehensive test coverage in `scripts/test_topic_tagging_direct.py`
  - Verified PostgreSQL compatibility in `scripts/test_db_integration.py`

### Topic Search Functionality
- Implemented `TopicSearchService` in `app/services/topic_search.py`
  - Provides methods for searching topics based on message content
  - Retrieves messages for specific topics
  - Gets all topics for a user
  - Formats search results for API responses
- Created API endpoints in `app/api/routes/topic.py`
  - `/topics/search` - Search for topics based on a query
  - `/topics/{topic_id}/messages` - Get messages for a specific topic
  - `/topics/user/{user_id}` - Get all topics for a user
- Added comprehensive test coverage in `tests/test_topic_search.py`
- Created example script in `scripts/test_topic_search.py`

### Topic Relevance Scoring
- Implemented advanced relevance scoring algorithm in `MemoryQueryRepository.get_topics_with_advanced_relevance`
  - Considers multiple factors for more accurate topic relevance:
    - Full-text search relevance (PostgreSQL ts_rank)
    - Topic frequency (how often the topic appears in user messages)
    - Recency (more recent topics get higher scores)
    - Direct keyword matches between query and topic name
- Added `search_topics_advanced` method to `TopicSearchService`
- Created new API endpoint at `/topics/search/advanced`
- Added comprehensive test coverage in `tests/test_topic_relevance.py`
- Created example script in `scripts/test_topic_relevance.py` for demonstration

### Topic Memory Retrieval
- Implemented `TopicMemoryService` in `app/services/topic_memory_service.py`
  - Provides methods for retrieving memory context based on topics
  - Retrieves memory context based on queries
  - Formats topic-based memory for chat completions
  - Supports comprehensive memory context retrieval
- Created API endpoints in `app/api/routes/memory.py`
  - `/memory/context` - Retrieve complete memory context for a chat completion
  - `/memory/topics` - Retrieve topic-based memory context
  - `/memory/topics/{topic_id}` - Retrieve memory context for a specific topic
  - `/memory/comprehensive` - Retrieve comprehensive memory context
  - `/memory/query/detect` - Detect if a query is asking about past conversations
- Updated `memory_context_service.py` to use advanced topic relevance scoring

### Memory Context Builder
- Implemented `MemoryContextBuilder` class in `app/core/memory_context_service.py`
  - Detects memory-related queries using regex patterns and keyword matching
  - Extracts topics from queries with integration to existing `TopicExtractor`
  - Assembles memory context from user facts, recent history, and topic memories
  - Prioritizes memories for memory-specific queries
  - Maintains backward compatibility with existing function-based approach
- Implemented memory prioritization logic:
  - `_prioritize_facts_by_topics`: Scores and prioritizes user facts based on query topics
  - `_prioritize_recent_memories`: Filters and prioritizes recent memories based on query content
  - `_prioritize_topic_memories`: Adjusts topic memories based on query topics
  - `_classify_memory_query_type`: Classifies memory queries into specific types (recall_verification, content_recall, temporal_recall, etc.)
- Created comprehensive test coverage:
  - `tests/test_memory_query_detection.py`: Tests for memory query detection and topic extraction
  - `tests/test_memory_prioritization.py`: Tests for memory prioritization logic and query classification
- Added example script in `scripts/test_memory_detection.py`
  - Demonstrates memory query detection without requiring database access
  - Shows topic extraction from various types of queries
  - Provides a simple way to test memory context builder functionality
- Added comprehensive test coverage in `tests/test_topic_memory_service.py`
- Created example script in `scripts/test_topic_memory.py` for demonstration

### Testing
- Direct tests for topic extraction, tagging, and search
- Integration tests with PostgreSQL database
- Test coverage for edge cases and error conditions
- Performance testing for database operations

## Current Work Focus

- Planning and documentation for the Python + FastAPI + PostgreSQL backend rebuild.
- Defining system architecture and Optimized memory retrieval queries: Implemented and tested (production-ready).strategies.
- Preparing for Firestore data migration.
- Python version: 3.12.10 (Windows)
- Virtual environment: Created and activated successfully
- Dependencies installed: FastAPI, SQLModel, SQLAlchemy, psycopg2-binary, python-dotenv, black, isort, flake8
- requirements.txt restored to original stack, all packages installed without build errors
- Project is ready for environment variable configuration (.env.example and python-dotenv)

## Recent Changes

- Project brief and product context documentation established.
- Ported regex patterns from legacy code to `utils/fact_patterns.py` (Tier 1 User Facts)
- Node.js backend deprecated; frontend is complete and stable.

- Regex patterns for user fact extraction have been ported to `utils/fact_patterns.py` and validated with comprehensive test coverage in `tests/test_fact_patterns.py`
- User fact storage logic implemented and tested (facts extracted from messages are persisted to DB; duplicate handling verified)
- Relevance scoring for fact retrieval implemented and tested (via `MemoryQueryRepository.get_facts_with_relevance`)
- Memory context assembly service created for integrating relevant facts into chat context (`memory_context_service.py`)
- Conversation history service implemented with methods for retrieving conversation history and context management
- API endpoints created for retrieving conversation history, recent messages, and conversation context
- Memory context service updated to use conversation history service for improved context assembly
- Comprehensive test coverage added for conversation history service and API endpoints
- Topic extraction service implemented for Tier 3 memory with 100% test coverage
- Topic extraction supports 15+ categories with keyword-based matching
- Example implementation demonstrates topic extraction from sample messages
## Next Steps

1. Document system architecture and design patterns.
2. Specify technology stack and development setup.
3. Draft initial FastAPI backend structure.
4. Plan and document Firestore → PostgreSQL migration process.
5. Set up Railway deployment configuration.

## Active Decisions and Considerations

- Prioritize stateless API design and robust memory context assembly.
- Ensure compatibility with existing frontend event system.
- Use SQLModel or SQLAlchemy for ORM layer.
- Maintain clear, up-to-date documentation throughout development.
