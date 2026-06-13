# BurnSignal

> Stop discovering overruns in the postmortem.

Real-time budget burn and spend forecasting for engineering teams.

## Stack
- **Frontend:** Next.js 14 + TypeScript + Tailwind CSS (Vercel)
- **Backend:** FastAPI (Python) — Vercel serverless functions
- **Database:** Aurora PostgreSQL (Vercel Marketplace OIDC)
- **Auth:** Clerk

## Getting started
```bash
# 1. Clone and install
cd frontend && npm install
cd ../backend && pip install -r requirements.txt

# 2. Copy env
cp .env.example .env

# 3. Run migrations
cd backend && alembic upgrade head

# 4. Start dev servers
cd frontend && npm run dev        # :3000
cd backend && uvicorn app.main:app --reload  # :8000
```

## Project structure
See /frontend and /backend directories.
Built for H0: Hack the Zero Stack — Track 2 Monetizable B2B App.
