# Tech Context: Freya Backend

## Technologies Used

- **Backend:** Python 3.11+, FastAPI, Firebase Admin SDK, Firestore, Uvicorn, python-dotenv
- **Frontend:** React 18, Next.js 14 (App Router), Tailwind CSS, shadcn/ui, Framer Motion (already built)
- **AI Integration:** OpenAI API (GPT-4.1 Mini fine-tuned model)
- **Storage:** Firebase/Firestore (production database), no PostgreSQL migration needed

## Development Setup

### Core Dependencies
- Python 3.11+ (macOS)
- FastAPI for the web framework
- Firebase Admin SDK for database operations
- Google Cloud Firestore for data persistence
- python-dotenv for environment management
- No database migrations needed (using existing Firestore)

### Development Tools
- black, isort, flake8 for code formatting and linting
- unittest for testing (no pytest dependency)
- Uvicorn as the ASGI server
- Simple test scripts for practical testing

### Environment
- Virtual environment: Working and activated
- All dependencies installed successfully with no build errors
- requirements.txt restored to the original stack
- Environment variables configured via .env file

### Infrastructure
- Firebase/Firestore (existing production database)
- GitHub for version control
- Node.js and pnpm for frontend (already complete)
- No additional database setup required

### Topic Extraction
- Implemented in `app/services/topic_extraction.py`
- Test coverage in `tests/test_topic_extraction.py`
- Example usage in `examples/topic_extraction_demo.py`

## Technical Constraints

- Backend must be stateless and compatible with browser event system
- Uses existing Firestore database (no migration needed)
- Ensure secure handling of API keys and user data
- Maintain compatibility with existing frontend
- Follow simplified approach - avoid unnecessary complexity

## Dependencies

### Backend
- **Web Framework**: FastAPI
- **Database**: Firebase Admin SDK, google-cloud-firestore
- **Development**: black, isort, flake8, unittest
- **AI**: OpenAI Python SDK (v1.17.0+)
- **Utilities**: python-dotenv, pydantic, python-multipart
- **Real-time**: sse-starlette for Server-Sent Events

### OpenAI Integration
- **Core**: OpenAI Python SDK for API communication
- **Model**: Fine-tuned GPT-4.1 Mini (ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj)
- **Features**: Retry logic, memory context injection, streaming support
- **Error Handling**: Exponential backoff for rate limits and API errors
- **Structure**: Service-oriented design with dependency injection

### Topic Extraction
- **Core**: Built-in Python re module for regex
- **Testing**: pytest, pytest-cov
- **Documentation**: Standard Python docstrings

### Frontend
- (Already managed in the frontend codebase)
