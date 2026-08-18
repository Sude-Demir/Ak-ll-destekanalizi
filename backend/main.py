from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import drafts, public, tickets, webhooks

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


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
