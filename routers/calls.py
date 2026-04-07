from fastapi import APIRouter, HTTPException, Header
from models import StartCampaignRequest
from database import supabase
from services.twilio_service import make_call
import threading
import time

router = APIRouter()

def get_politician_id(authorization: str) -> str:
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        return user.user.id
    except:
        raise HTTPException(status_code=401, detail="Unauthorized")

def process_calls_in_background(campaign_id: str, contacts: list, template: dict, campaign_lang: str):
    """
    Runs in background thread — triggers calls in batches of 10
    with 1 second delay between batches (10 calls/sec = safe for Twilio)
    """
    BATCH_SIZE = 10
    DELAY_BETWEEN_BATCHES = 1  # seconds

    for i in range(0, len(contacts), BATCH_SIZE):
        batch = contacts[i:i + BATCH_SIZE]
        threads = []

        for contact in batch:
            t = threading.Thread(
                target=trigger_single_call,
                args=(contact, template, campaign_lang, campaign_id)
            )
            threads.append(t)
            t.start()

        # Wait for all threads in batch to complete
        for t in threads:
            t.join()

        # Delay between batches to respect Twilio rate limits
        time.sleep(DELAY_BETWEEN_BATCHES)

    # Mark campaign as completed if all done
    supabase.table("campaigns")\
        .update({"status": "completed"})\
        .eq("id", campaign_id)\
        .execute()

def trigger_single_call(contact: dict, template: dict, campaign_lang: str, campaign_id: str):
    """Triggers a single call and logs it"""
    try:
        if campaign_lang == "kn":
            audio_url = template.get("audio_url_kn")
        elif campaign_lang == "hi":
            audio_url = template.get("audio_url_hi")
        elif campaign_lang == "both":
            contact_lang = contact.get("language", "kn")
            if contact_lang == "hi":
                audio_url = template.get("audio_url_hi")
            else:
                audio_url = template.get("audio_url_kn")
        else:
            audio_url = template.get("audio_url_kn") or template.get("audio_url_hi")

        if not audio_url:
            supabase.table("contacts")\
                .update({"status": "failed"})\
                .eq("id", contact["id"])\
                .execute()
            return

        call_sid = make_call(
            to=contact["phone"],
            audio_url=audio_url,
            contact_id=contact["id"],
            campaign_id=campaign_id
        )

        supabase.table("call_logs").insert({
            "contact_id": contact["id"],
            "campaign_id": campaign_id,
            "twilio_sid": call_sid,
            "status": "initiated"
        }).execute()

    except Exception as e:
        supabase.table("contacts")\
            .update({"status": "failed"})\
            .eq("id", contact["id"])\
            .execute()

# POST start campaign
@router.post("/start")
def start_campaign(request: StartCampaignRequest, authorization: str = Header(...)):
    get_politician_id(authorization)
    campaign_id = request.campaign_id

    # Get campaign details
    campaign = supabase.table("campaigns")\
        .select("*, script_templates(*)")\
        .eq("id", campaign_id)\
        .single()\
        .execute().data

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get all pending contacts
    contacts = supabase.table("contacts")\
        .select("*")\
        .eq("campaign_id", campaign_id)\
        .eq("status", "pending")\
        .execute().data

    if not contacts:
        raise HTTPException(status_code=400, detail="No pending contacts found")

    # Update campaign status to active immediately
    supabase.table("campaigns")\
        .update({"status": "active"})\
        .eq("id", campaign_id)\
        .execute()

    # Start background thread — API returns immediately
    thread = threading.Thread(
        target=process_calls_in_background,
        args=(campaign_id, contacts, campaign["script_templates"], campaign.get("language", "kn"))
    )
    thread.daemon = True
    thread.start()

    return {
        "message": "Campaign started in background",
        "total_contacts": len(contacts),
        "estimated_time_minutes": round(len(contacts) / 10 / 60, 1)
    }

# POST pause
@router.post("/pause/{campaign_id}")
def pause_campaign(campaign_id: str, authorization: str = Header(...)):
    get_politician_id(authorization)
    supabase.table("campaigns")\
        .update({"status": "paused"})\
        .eq("id", campaign_id)\
        .execute()
    return {"message": "Campaign paused"}

# POST resume
@router.post("/resume/{campaign_id}")
def resume_campaign(campaign_id: str, authorization: str = Header(...)):
    get_politician_id(authorization)

    # Get pending contacts and restart
    campaign = supabase.table("campaigns")\
        .select("*, script_templates(*)")\
        .eq("id", campaign_id)\
        .single()\
        .execute().data

    contacts = supabase.table("contacts")\
        .select("*")\
        .eq("campaign_id", campaign_id)\
        .eq("status", "pending")\
        .execute().data

    supabase.table("campaigns")\
        .update({"status": "active"})\
        .eq("id", campaign_id)\
        .execute()

    if contacts:
        thread = threading.Thread(
            target=process_calls_in_background,
            args=(campaign_id, contacts, campaign["script_templates"], campaign.get("language", "kn"))
        )
        thread.daemon = True
        thread.start()

    return {"message": "Campaign resumed", "remaining_contacts": len(contacts)}