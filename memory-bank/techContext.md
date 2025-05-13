# Tech Context: Freya Backend

## Technologies Used

- **Backend:** Python 3.11+, FastAPI, SQLModel or SQLAlchemy, PostgreSQL, Uvicorn, python-dotenv, Alembic
- **Frontend:** React 18, Next.js 14 (App Router), Tailwind CSS, shadcn/ui, Framer Motion (already built)
- **AI Integration:** OpenAI API (GPT-4.1 Mini fine-tuned model)
- **Storage:** PostgreSQL (hosted on Railway), optional Cloudinary/UploadThing for media

## Development Setup

- Python virtual environment for backend development
- PostgreSQL database instance (local for dev, Railway for prod)
- Environment variables managed via .env files
- Alembic for database migrations
- GitHub Actions for CI/CD pipeline
- Node.js and pnpm for frontend (already complete)

## Technical Constraints

- Backend must be stateless and compatible with browser event system
- Must support migration from Firestore to PostgreSQL
- Ensure secure handling of API keys and user data
- Maintain compatibility with existing frontend

## Dependencies

- FastAPI, SQLModel/SQLAlchemy, Uvicorn, python-dotenv, Alembic, psycopg2 or asyncpg
- OpenAI Python SDK
- (Frontend dependencies already managed)
