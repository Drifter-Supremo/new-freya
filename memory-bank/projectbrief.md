# Project Brief: Freya Backend Rebuild (Python \+ SQL)

## Project Name

**Freya AI Companion — Backend Rebuild**

## Project Summary

Freya is a fine-tuned GPT-4.1 Mini AI companion designed with a unique emotional persona and personal memory system. The frontend UI is a cyberpunk-inspired, single-screen holographic cockpit built with React, Tailwind CSS, shadcn/ui, and Framer Motion. The current backend, built with Node.js and Firebase, has reached its limits due to instability, security issues, and integration challenges. This project will fully rebuild Freya’s backend in Python using FastAPI and PostgreSQL, ensuring stability, better memory management, and long-term maintainability.

## Goals

* Recreate Freya’s backend in Python using FastAPI  
* Replace Firebase with a structured PostgreSQL database  
* Preserve the three-tier memory architecture (User Facts, Recent History, Topic Memory)  
* Maintain compatibility with the existing frontend via custom browser events  
* Integrate Freya’s fine-tuned GPT-4.1 Mini model for all chat completions  
* Migrate existing Firestore data into PostgreSQL  
* Deploy on Railway using the existing Hobby plan

## Tech Stack

**Frontend:** (already built)

* React 18  
* Next.js 14 (App Router)  
* Tailwind CSS  
* shadcn/ui  
* Framer Motion

**Backend (new):**

* Python 3.11+  
* FastAPI  
* SQLModel or SQLAlchemy  
* PostgreSQL  
* Uvicorn  
* python-dotenv  
* Alembic (for migrations)

**AI Integration:**

* OpenAI API (GPT-4.1 Mini fine-tuned model)

**Storage:**

* PostgreSQL (hosted on Railway)  
* Optional: Cloudinary or UploadThing for media storage

**Event System:**

* Browser event-based communication using `freya:listening`, `freya:thinking`, `freya:reply`

## Key Features

* Stateless FastAPI endpoints for sending/receiving messages  
* Memory context assembly engine to inject Freya’s memory into API calls  
* Full-text topic search using PostgreSQL  
* Firestore migration tooling  
* Structured logging, validation, and fallback error handling  
* CI/CD pipeline with GitHub Actions

## Deliverables

* Fully functional FastAPI backend connected to PostgreSQL  
* Re-implementation of memory system (facts, history, topics)  
* API route that accepts user messages and returns GPT-4.1 Mini completions  
* Frontend integration through browser event dispatchers  
* Complete Firestore → PostgreSQL data migration  
* Deployment on Railway with environment management  
* Internal developer documentation and API references

## Current Status

Frontend complete. GPT-4.1 Mini fine-tuned model complete. Node.js backend deprecated. Python \+ SQL backend in planning phase.

## Primary Owner

**Sencere**  
