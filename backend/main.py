from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import agent_invites, analytics, drafts, me, public, tickets, webhooks

app = FastAPI(title="Akıllı Destek Asistanı API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router)
app.include_router(drafts.router)
app.include_router(webhooks.router)
app.include_router(public.router)
app.include_router(me.router)
app.include_router(agent_invites.router)
app.include_router(analytics.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
