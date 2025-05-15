# System Patterns: Freya Backend

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

- Repository Query Pattern: Dedicated repository for efficient user/topic/fact/message retrieval using SQLAlchemy joins and eager loading. All datetime fields use timezone-aware UTC datetimes for future compatibility.
- Service layer for business logic and memory context assembly.
- DTOs (Data Transfer Objects) for API request/response validation.
- Error handling middleware for consistent fallback behavior.
- Regex patterns for user fact extraction ported to `utils/fact_patterns.py` with comprehensive test coverage in `tests/test_fact_patterns.py`

## Component Relationships

- API endpoints interact with service layer, which manages memory and database operations.
- Memory context engine aggregates data from all three memory tiers.
- Frontend communicates with backend via browser events and REST endpoints.
- Logging and error handling are centralized for maintainability.
