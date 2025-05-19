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

### Backend Commands
```bash
# Create/activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run the backend
uvicorn app.main:app --reload
# Or use the helper script:
python scripts/run_server.py

# Database setup
python scripts/setup_test_db.py  # Create test database
alembic upgrade head             # Run migrations

# Testing
pytest tests/                    # Run all tests
pytest tests/test_api.py -k test_health  # Run specific test

# New test scripts for Phase 4
python scripts/test_all.py       # Run comprehensive integration tests
python scripts/create_test_user.py  # Create test user for testing
python scripts/test_chat_simple.py  # Test chat endpoint directly
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
- Phase 4: ✅ Mostly Completed (OpenAI Integration & API Endpoints)
  - `/chat/completions` endpoint fully implemented and tested
  - All 5 integration tests passing
  - Memory context injection working
  - Conversation management working
  - Remaining: Additional conversation management endpoints
- Phase 5-8: Frontend Integration, Migration, Testing, Deployment (pending)

### Recent Achievements (Phase 4)
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