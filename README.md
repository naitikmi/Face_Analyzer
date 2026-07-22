# Atelier — Face & Style Analysis

A camera-based Progressive Web App: take or upload a photo, get a read on your
face shape, and curated beard, hair, and glasses recommendations built for
your proportions instead of a generic average.

## How it works

- **Backend** (`backend/`) — FastAPI + [MediaPipe](https://ai.google.dev/edge/mediapipe) for face detection and 478-point
  landmark extraction, geometric face-shape classification, and rule-based
  beard/hair/glasses recommenders. Optionally calls Gemini's image-editing
  model for a "preview this style on me" feature. Nothing is persisted —
  photos are processed in memory and discarded once the response is sent.
- **Frontend** (`frontend/`) — Next.js 16 + TypeScript + Tailwind, installable
  as a PWA (Serwist-powered service worker), with `getUserMedia` camera
  capture and a graceful file-upload fallback.

## Running locally

```bash
# backend
cd backend
pip install -r requirements.txt
uvicorn face_analyzer.api.app:app --reload --port 8000

# frontend (separate terminal)
cd frontend
npm install
npm run dev
```

The frontend expects the backend at `http://localhost:8000` by default (see
`frontend/.env.example`). Optional: set `GEMINI_API_KEY` in `backend/.env`
(see `backend/.env.example`) to enable the "preview on me" feature — every
other feature works without it.

## Deploying

See [DEPLOY.md](DEPLOY.md) — backend on Render, frontend on Vercel, both
auto-deploying from `main`.
