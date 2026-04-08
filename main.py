from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="AI Calling Agent API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://ai-calling-agent-ten.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from routers import templates, campaigns, contacts, calls, twiml

app.include_router(templates.router, prefix="/templates", tags=["templates"])
app.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
app.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
app.include_router(calls.router, prefix="/calls", tags=["calls"])
app.include_router(twiml.router, prefix="/twiml", tags=["twiml"])

@app.get("/")
def root():
    return {"status": "ok", "message": "AI Calling Agent API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}