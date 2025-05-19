# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

\### Critical Rules - DO NOT VIOLATE

\- \*\*ALWAYS start every new task with reading the CLAUDE.md

\- \*\*NEVER create mock data or simplified components\*\* unless explicitly told to do so

\- \*\*NEVER replace existing complex components with simplified versions\*\* - always fix the actual problem

\- \*\*ALWAYS work with the existing codebase\*\* - do not create new simplified alternatives

\- \*\*ALWAYS find and fix the root cause\*\* of issues instead of creating workarounds

\- When debugging issues, focus on fixing the existing implementation, not replacing it

\- When something doesn't work, debug and fix it - don't start over with a simple version

\- \*\*ALWAYS check ALL /memory-bank DOCS before making changes\*\* 

\- NEVER complete multiple tasks in a row unless told to do so ALWAYS complete 1 task at a time then stop to regroup with me.

\- ALWAYS update ALL relevant/memory-bank docs after every successful task

\### Development Environment - IMPORTANT

\- **Operating System**: Windows with WSL (Windows Subsystem for Linux)
\- **Python**: Using Windows Python from WSL (venv/Scripts/python.exe)
\- **Virtual Environment**: Located at `venv/` in project root
\- **Database**: PostgreSQL (must be running for all operations)

\### Quick Start Guide for Testing

1. **Activate Virtual Environment (Windows from WSL)**:
   ```bash
   cd "/mnt/c/Users/drift/Documents/Cline Projects/new-freya-who-this"
   # Use Windows Python executable from WSL:
   venv/Scripts/python.exe
   ```

2. **Start the FastAPI Server**:
   ```bash
   # Option 1: Using the helper script
   venv/Scripts/python.exe scripts/run_server.py
   
   # Option 2: Direct uvicorn
   venv/Scripts/python.exe -m uvicorn app.main:app --reload
   ```

3. **Run Tests**:
   ```bash
   # Run all tests
   venv/Scripts/python.exe -m pytest tests/ -v
   
   # Run specific test file
   venv/Scripts/python.exe -m pytest tests/test_conversation_endpoints.py -v
   
   # Run comprehensive integration tests
   venv/Scripts/python.exe scripts/test_all.py
   ```

\### Common Import Fixes

When imports fail, check these common issues:
1. `init_db` is in `app.core.init_db`, not `app.core.db`
2. User model has `username` field, not `name`
3. User model requires `hashed_password` field
4. All IDs are integers, not UUIDs

\### Test Data Patterns

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

\### Database Migrations

When adding new columns or database features:
```bash
# Create new migration
venv/Scripts/python.exe -m alembic revision -m "description"

# Run migrations
venv/Scripts/python.exe -m alembic upgrade head
```

\### PostgreSQL Full-Text Search

- Messages table has `content_tsv` column for FTS
- Trigger automatically populates tsvector on insert/update
- Search queries use `plainto_tsquery()` for text matching

\### TypeScript and Linting

\- ALWAYS add explicit types to all function parameters, variables, and return types

\- ALWAYS run npm build\ or whichever appropriate linter command before considering any code changes complete

\- Fix all linter and TypeScript errors immediately - don't leave them for the user to fix

\- When making changes to multiple files, check each one for type errors



\### Web Access and MCP Tools

\- Use the built-in WebFetch tool to access web content using the following syntax:
  ```
  WebFetch({
    url: "https://example.com/path",
    prompt: "Extract key information about [specific topic]"
  })
  ```

\- The WebFetch tool can be used to:
  - Retrieve documentation
  - Research APIs and libraries
  - Access technical resources
  - View content from URLs the user provides

\- If the user references specific URLs, always use WebFetch to retrieve and process the content

\- Context7 MCP is available for vector storage and retrieval augmented generation:
  - This provides advanced RAG capabilities for knowledge management
  - Can be used for semantic search across documentation
  - Enables more context-aware responses based on stored information
  - Works well for persisting information across sessions

## Project Overview

Freya AI Companion is a fine-tuned GPT-4.1 Mini AI chatbot with a unique emotional persona and tiered memory system. The project consists of:

- **Backend**: Python 3.11+, FastAPI, PostgreSQL, SQLAlchemy/SQLModel
- **Frontend**: React 18, Next.js 14, Tailwind CSS, shadcn/ui, Framer Motion  
- **AI Model**: Fine-tuned GPT-4.1 Mini: "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj"
- **Features**: Multi-tiered memory system (user facts, recent history, topics), OpenAI integration, RESTful API

## Common Development Commands

### Backend Commands (Windows with WSL)
```bash
# Path to project (ALWAYS USE QUOTES for paths with spaces)
cd "/mnt/c/Users/drift/Documents/Cline Projects/new-freya-who-this"

# Python executable (ALWAYS use this path)
venv/Scripts/python.exe

# Install dependencies
venv/Scripts/python.exe -m pip install -r requirements.txt

# Run the backend
venv/Scripts/python.exe -m uvicorn app.main:app --reload
# Or use the helper script:
venv/Scripts/python.exe scripts/run_server.py

# Database setup
venv/Scripts/python.exe scripts/setup_test_db.py  # Create test database
venv/Scripts/python.exe -m alembic upgrade head   # Run migrations

# Testing
venv/Scripts/python.exe -m pytest tests/ -v       # Run all tests
venv/Scripts/python.exe -m pytest tests/test_api.py -k test_health  # Specific test

# Quick test scripts
venv/Scripts/python.exe scripts/test_all.py       # Comprehensive integration tests
venv/Scripts/python.exe scripts/create_test_user.py  # Create test user
venv/Scripts/python.exe scripts/test_chat_simple.py  # Test chat endpoint
venv/Scripts/python.exe scripts/test_conversation_endpoints.py  # Test conversations
```

### Quick Testing Workflow
```bash
# Terminal 1: Start the server
cd "/mnt/c/Users/drift/Documents/Cline Projects/new-freya-who-this"
venv/Scripts/python.exe scripts/run_server.py

# Terminal 2: Run tests
cd "/mnt/c/Users/drift/Documents/Cline Projects/new-freya-who-this"
venv/Scripts/python.exe scripts/test_all.py  # Quick integration tests
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

3. **Topic Memory (Tier 3)**: Long-term topical memories using PostgreSQL full-text search
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

### Database Schema
Models defined in `app/models/`:
- `user.py`: User management
- `conversation.py`: Conversation tracking  
- `message.py`: Message storage
- `topic.py`: Topic and message-topic associations
- `userfact.py`: User fact storage

Uses PostgreSQL with full-text search capabilities (TSVECTOR columns).

### API Structure
Routes organized in `app/api/routes/`:
- `/health`: Basic health check
- `/db_health`: Database connectivity check
- `/conversations`: Conversation management
- `/user_facts`: User fact CRUD operations
- `/topics`: Topic management and search
- `/memory`: Memory context retrieval

### Testing Strategy
- Unit tests for all services and repositories
- Integration tests for PostgreSQL-specific features
- Mock OpenAI integration tests  
- Test fixtures in `tests/conftest.py`
- Development database used for testing

### Environment Configuration
Required environment variables (see `.env.example`):
- `OPENAI_API_KEY`: OpenAI API access
- `POSTGRES_URL`: PostgreSQL connection string
- `LOG_LEVEL`: Optional logging configuration

### Key Implementation Notes
1. **PostgreSQL-specific features**: The app uses PostgreSQL's full-text search, requiring actual PostgreSQL instances for testing (not SQLite)
2. **Memory prioritization**: Implemented scoring algorithms for relevance-based memory retrieval
3. **Error handling**: Centralized error handling in `app/core/errors.py`
4. **Logging**: Configured via `app/core/config.py` 
5. **CORS**: Development configuration allows all origins

### Progress Tracking
Detailed task breakdown in `memory-bank/tasks.md` tracks implementation phases:
- Phase 1-3: ✅ Completed (Setup, Database, Memory System)
- Phase 4: ✅ Completed (OpenAI Integration & API Endpoints)
  - `/chat/completions` endpoint fully implemented and tested
  - All 5 integration tests passing
  - Memory context injection working
  - Conversation management endpoints all implemented
  - Full-text search working with PostgreSQL
- Phase 5-8: Frontend Integration, Migration, Testing, Deployment (pending)

### Recent Achievements (Phase 4) - Completed 2025-05-19
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
  - GET `/conversations/{user_id}/search` - Full-text search with PostgreSQL
  - DELETE `/conversations/{conversation_id}` - Delete with authorization
  - Fixed all existing endpoints for proper functioning
- **Added database migration** for tsvector trigger to support full-text search
- **All Phase 4 tests passing** - 11/11 conversation endpoint tests successful

### Troubleshooting Common Issues

1. **"python: command not found" in WSL**:
   - Always use `venv/Scripts/python.exe` (Windows Python)
   - Never use just `python` or `python3` in WSL

2. **Import errors with test files**:
   - Delete `__pycache__` directories if tests have same names as scripts
   - Use unique names for test files vs script files

3. **Database connection issues**:
   - Ensure PostgreSQL is running
   - Check `.env` file has correct `POSTGRES_URL`
   - Run migrations: `venv/Scripts/python.exe -m alembic upgrade head`

4. **Session/transaction issues in tests**:
   - Use dependency injection to override database sessions
   - Get object IDs before making requests: `user_id = test_user.id`
   - Don't rely on lazy loading in tests

5. **Full-text search not working**:
   - Ensure tsvector trigger migration has been run
   - Check that `content_tsv` column exists in messages table
   - Use `plainto_tsquery()` for searches, not plain LIKE

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