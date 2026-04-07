from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from database import supabase
from datetime import datetime

router = APIRouter()

# Twilio calls this to get the TwiML instructions (what to play)
@router.api_route("/{contact_id}", methods=["GET", "POST"])
def get_twiml(contact_id: str, audio_url: str, campaign_id: str):
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
    <Hangup/>
</Response>"""
    return Response(content=twiml, media_type="application/xml")

# Twilio calls this to report call status
@router.post("/status")
async def call_status(request: Request):
    form = await request.form()

    twilio_sid = form.get("CallSid")
    call_status = form.get("CallStatus")
    call_duration = form.get("CallDuration", 0)

    # Map Twilio status to our status
    status_map = {
        "completed": "called",
        "failed": "failed",
        "busy": "busy",
        "no-answer": "no_answer",
        "canceled": "failed"
    }
    our_status = status_map.get(call_status, "failed")

    # Find the call log by twilio_sid
    log = supabase.table("call_logs")\
        .select("*")\
        .eq("twilio_sid", twilio_sid)\
        .single()\
        .execute().data

    if not log:
        return Response(content="ok")

    contact_id = log["contact_id"]
    campaign_id = log["campaign_id"]

    # Update call log
    supabase.table("call_logs")\
        .update({
            "status": our_status,
            "duration": int(call_duration)
        })\
        .eq("twilio_sid", twilio_sid)\
        .execute()

    # Update contact status
    supabase.table("contacts")\
        .update({
            "status": our_status,
            "call_duration": int(call_duration),
            "called_at": datetime.utcnow().isoformat()
        })\
        .eq("id", contact_id)\
        .execute()

    # Update campaign counters
    campaign = supabase.table("campaigns")\
        .select("called, failed, busy, no_answer, total_contacts")\
        .eq("id", campaign_id)\
        .single()\
        .execute().data

    update_data = {}
    if our_status == "called":
        update_data["called"] = campaign["called"] + 1
    elif our_status == "failed":
        update_data["failed"] = campaign["failed"] + 1
    elif our_status == "busy":
        update_data["busy"] = campaign["busy"] + 1
    elif our_status == "no_answer":
        update_data["no_answer"] = campaign["no_answer"] + 1

    # Check if campaign is completed
    total_done = (
        campaign["called"] +
        campaign["failed"] +
        campaign["busy"] +
        campaign["no_answer"] + 1
    )
    if total_done >= campaign["total_contacts"]:
        update_data["status"] = "completed"
        update_data["completed_at"] = datetime.utcnow().isoformat()

    supabase.table("campaigns")\
        .update(update_data)\
        .eq("id", campaign_id)\
        .execute()

    return Response(content="ok")