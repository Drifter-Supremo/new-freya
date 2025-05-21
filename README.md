# Freya Backend Rebuild

This repository contains the code for rebuilding the Freya AI chatbot backend using Python and Firebase/Firestore, designed to work seamlessly with the existing React frontend.

## Project Overview
- **Backend:** Python 3.11+, FastAPI, Firebase/Firestore
- **Frontend:** React (existing)
- **Features:**
  - Multi-tiered memory system (user facts, recent history, topics)
  - OpenAI GPT-4.1 mini integration
  - Firebase/Firestore integration with existing data
  - Server-Sent Events (SSE) for real-time communication
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

### 3. Set up Firebase/Firestore
- Download Firebase service account credentials from Firebase Console (see `FIREBASE_SETUP.md`)
- Place credentials file as `freya-ai-chat-firebase-adminsdk-fbsvc-0af7f65b8e.json` in project root
- Firestore collections should include: `userFacts`, `conversations`, `messages`

### 4. Environment Variables  
- Copy `.env.example` to `.env` and fill in your configuration (OpenAI API key, Firebase config, etc.)

### 5. Run the backend
```sh
uvicorn app.main:app --reload
# Or use the helper script:
python scripts/run_server.py
```

### 6. Testing
```sh
# Test Firebase connectivity and data retrieval
python scripts/test_firebase_connection.py

# Test complete Firebase chat API with real data
python scripts/test_firebase_chat.py

# Test Server-Sent Events (SSE) functionality
python scripts/test_event_dispatcher.py
```

## Documentation
- See `memory-bank/tasks.md` for project phases and detailed tasks
- See `memory-bank/projectbrief.md` for the project brief and goals

---

For more details, refer to the documentation in the `memory-bank` directory.

---

*Created and maintained by Drifter-Supremo and contributors.*
