# How to Start Freya AI System

## Quick Start (One Command)

```bash
cd "/Volumes/Low Key Genius Hub/Projects/new-freya-who-this/freya-ui"
npm run dev
```

This starts both servers simultaneously:
- **Backend (FastAPI)**: http://localhost:8001
- **Frontend (Next.js)**: http://localhost:3000

## Access the Application

Open your browser and go to: **http://localhost:3000**

You'll see the Freya hologram interface where you can start chatting!

## Manual Start (If Needed)

### Terminal 1 - Backend
```bash
cd "/Volumes/Low Key Genius Hub/Projects/new-freya-who-this"
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8001
```

### Terminal 2 - Frontend
```bash
cd "/Volumes/Low Key Genius Hub/Projects/new-freya-who-this/freya-ui"
npm run frontend
```

## Troubleshooting

- If ports are occupied, kill processes: `pkill -f uvicorn`
- Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- Check browser console (F12) for errors
- Backend API docs available at: http://localhost:8001/docs