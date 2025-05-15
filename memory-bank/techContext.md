# Tech Context: Freya Backend

## Technologies Used

- **Backend:** Python 3.11+, FastAPI, SQLModel or SQLAlchemy, PostgreSQL, Uvicorn, python-dotenv, Alembic
- **Frontend:** React 18, Next.js 14 (App Router), Tailwind CSS, shadcn/ui, Framer Motion (already built)
- **AI Integration:** OpenAI API (GPT-4.1 Mini fine-tuned model)
- **Storage:** PostgreSQL (hosted on Railway), optional Cloudinary/UploadThing for media

## Development Setup

### Core Dependencies
- Python 3.12.10 (Windows)
- FastAPI for the web framework
- SQLAlchemy/SQLModel for ORM
- PostgreSQL with psycopg2-binary driver
- python-dotenv for environment management
- Alembic for database migrations

### Development Tools
- black, isort, flake8 for code formatting and linting
- pytest for testing
- Uvicorn as the ASGI server

### Environment
- Virtual environment: Working and activated
- All dependencies installed successfully with no build errors
- requirements.txt restored to the original stack
- Environment variables configured via .env file

### Infrastructure
- PostgreSQL database instance (local for dev, Railway for prod)
- GitHub Actions for CI/CD pipeline
- Node.js and pnpm for frontend (already complete)

### Topic Extraction
- Implemented in `app/services/topic_extraction.py`
- Test coverage in `tests/test_topic_extraction.py`
- Example usage in `examples/topic_extraction_demo.py`

## Technical Constraints

- Backend must be stateless and compatible with browser event system
- Must support migration from Firestore to PostgreSQL
- Ensure secure handling of API keys and user data
- Maintain compatibility with existing frontend

## Dependencies

### Backend
- **Web Framework**: FastAPI
- **Database**: SQLAlchemy, SQLModel, psycopg2-binary, asyncpg
- **Development**: black, isort, flake8, pytest
- **AI**: OpenAI Python SDK
- **Utilities**: python-dotenv, pydantic, python-multipart

### Topic Extraction
- **Core**: Built-in Python re module for regex
- **Testing**: pytest, pytest-cov
- **Documentation**: Standard Python docstrings

### Frontend
- (Already managed in the frontend codebase)
