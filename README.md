# Freya Backend Rebuild

This repository contains the code for rebuilding the Freya AI chatbot backend using Python and PostgreSQL, designed to work seamlessly with the existing React frontend.

## Project Overview
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy/SQLModel, PostgreSQL
- **Frontend:** React (existing)
- **Features:**
  - Multi-tiered memory system (user facts, recent history, topics)
  - OpenAI GPT-4.1 mini integration
  - RESTful API and WebSocket support
  - Full compatibility with frontend event system

## Getting Started

### 1. Clone the repository
```sh
git clone https://github.com/Drifter-Supremo/new-freya.git
cd new-freya
```

### 2. Set up Python environment
- Install Python 3.11+
- Create and activate a virtual environment:
  ```sh
  python -m venv venv
  # On Windows:
  venv\Scripts\activate
  # On Mac/Linux:
  source venv/bin/activate
  ```
- Install dependencies:
  ```sh
  pip install -r requirements.txt
  ```

### 3. Set up PostgreSQL
- Install PostgreSQL and pgAdmin if not already installed
- Create a local development database (see `memory-bank/tasks.md` for schema)

### 4. Environment Variables
- Copy `.env.example` to `.env` and fill in your configuration (OpenAI API key, database URL, etc.)

### 5. Run the backend
```sh
uvicorn app.main:app --reload
# Or use the helper script:
python scripts/run_server.py
```

### 6. Testing
```sh
# Run comprehensive test suite (starts server and runs all tests)
python scripts/test_all.py

# Run specific pytest unit tests
python -m pytest tests/test_chat_simple.py -v

# Create a test user
python scripts/create_test_user.py

# Test the chat endpoint directly
python scripts/test_chat_simple.py
```

## Documentation
- See `memory-bank/tasks.md` for project phases and detailed tasks
- See `memory-bank/projectbrief.md` for the project brief and goals

---

For more details, refer to the documentation in the `memory-bank` directory.

---

*Created and maintained by Drifter-Supremo and contributors.*
