from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="AI Calling Agent API", version="1.0.0")

# CORS - allows Next.js frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from routers import templates
app.include_router(templates.router, prefix="/templates", tags=["templates"])

from routers import templates, campaigns
app.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])

from routers import templates, campaigns, contacts
app.include_router(contacts.router, prefix="/contacts", tags=["contacts"])

from routers import templates, campaigns, contacts, calls
app.include_router(calls.router, prefix="/calls", tags=["calls"])

from routers import templates, campaigns, contacts, calls, twiml
app.include_router(calls.router, prefix="/calls", tags=["calls"])
app.include_router(twiml.router, prefix="/twiml", tags=["twiml"])
# (we'll add these as we build each one)
# from routers import campaigns, contacts, calls, twiml
# app.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
# app.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
# app.include_router(calls.router, prefix="/calls", tags=["calls"])
# app.include_router(twiml.router, prefix="/twiml", tags=["twiml"])

@app.get("/")
def root():
    return {"status": "ok", "message": "AI Calling Agent API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}