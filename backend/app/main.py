from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    auth, orgs, departments, projects, phases,
    budgets, time_entries, costs, forecast,
    integrations, dashboard, historical
)

app = FastAPI(title="BurnSignal API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://burnsignal.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(orgs.router, prefix="/api/orgs", tags=["orgs"])
app.include_router(departments.router, prefix="/api/orgs", tags=["departments"])
app.include_router(projects.router, prefix="/api/orgs", tags=["projects"])
app.include_router(phases.router, prefix="/api/orgs", tags=["phases"])
app.include_router(budgets.router, prefix="/api/orgs", tags=["budgets"])
app.include_router(time_entries.router, prefix="/api/orgs", tags=["time_entries"])
app.include_router(costs.router, prefix="/api/orgs", tags=["costs"])
app.include_router(forecast.router, prefix="/api/orgs", tags=["forecast"])
app.include_router(integrations.router, prefix="/api/orgs", tags=["integrations"])
app.include_router(dashboard.router, prefix="/api/orgs", tags=["dashboard"])
app.include_router(historical.router, prefix="/api/orgs", tags=["historical"])

@app.get("/health")
def health():
    return {"status": "ok"}
