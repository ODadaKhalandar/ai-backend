from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# --- Auth ---
class PoliticianCreate(BaseModel):
    name: str
    email: str
    password: str
    constituency: Optional[str] = None
    state: Optional[str] = None

class PoliticianLogin(BaseModel):
    email: str
    password: str

# --- Templates ---
class TemplateCreate(BaseModel):
    name: str
    script_kn: Optional[str] = None
    script_hi: Optional[str] = None

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    script_kn: Optional[str] = None
    script_hi: Optional[str] = None

# --- Campaigns ---
class CampaignCreate(BaseModel):
    name: str
    template_id: str
    language: str = "kn"  # kn / hi / both

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None

# --- Contacts ---
class ContactCreate(BaseModel):
    name: Optional[str] = None
    phone: str
    language: str = "kn"

# --- Calls ---
class StartCampaignRequest(BaseModel):
    campaign_id: str