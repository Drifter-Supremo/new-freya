# Product Context: Freya AI Companion

## Why This Project Exists

Freya is designed to be a highly personalized AI companion with a unique emotional persona and persistent memory. The project aims to overcome the limitations of the previous Node.js/Firebase backend, which suffered from instability, security issues, and integration challenges.

## Problems Solved

- Provides a stable, secure, and maintainable backend using Python (FastAPI) and PostgreSQL.
- Enables advanced memory management with a three-tier memory architecture (User Facts, Recent History, Topic Memory).
- Ensures compatibility with a sophisticated cyberpunk-inspired frontend UI.
- Facilitates seamless integration with a fine-tuned GPT-4.1 Mini model for chat completions.
- Supports migration from Firestore to PostgreSQL for data continuity.

## How It Should Work

- Stateless FastAPI endpoints handle all message exchanges.
- Memory context is dynamically assembled and injected into API calls.
- PostgreSQL enables full-text topic search and structured data storage.
- The backend communicates with the frontend via custom browser events (`freya:listening`, `freya:thinking`, `freya:reply`).
- The system is deployed on Railway for reliable cloud hosting.

## User Experience Goals

- Fast, reliable, and emotionally engaging AI interactions.
- Persistent and contextually relevant memory for each user.
- Smooth, visually immersive frontend experience.
- Transparent and robust error handling.
- Easy developer onboarding and clear documentation.
