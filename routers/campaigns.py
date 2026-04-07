from fastapi import APIRouter, HTTPException, Header
from models import CampaignCreate, CampaignUpdate
from database import supabase

router = APIRouter()

def get_politician_id(authorization: str) -> str:
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        return user.user.id
    except:
        raise HTTPException(status_code=401, detail="Unauthorized")

# GET all campaigns
@router.get("/")
def get_campaigns(authorization: str = Header(...)):
    politician_id = get_politician_id(authorization)
    result = supabase.table("campaigns")\
        .select("*, script_templates(name)")\
        .eq("politician_id", politician_id)\
        .order("created_at", desc=True)\
        .execute()
    return result.data

# GET single campaign
@router.get("/{campaign_id}")
def get_campaign(campaign_id: str, authorization: str = Header(...)):
    politician_id = get_politician_id(authorization)
    result = supabase.table("campaigns")\
        .select("*, script_templates(name)")\
        .eq("id", campaign_id)\
        .eq("politician_id", politician_id)\
        .single()\
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return result.data

# POST create campaign
@router.post("/")
def create_campaign(campaign: CampaignCreate, authorization: str = Header(...)):
    politician_id = get_politician_id(authorization)

    data = {
        "politician_id": politician_id,
        "name": campaign.name,
        "template_id": campaign.template_id,
        "language": campaign.language,
        "status": "draft"
    }

    result = supabase.table("campaigns").insert(data).execute()
    return result.data[0]

# PUT update campaign
@router.put("/{campaign_id}")
def update_campaign(campaign_id: str, campaign: CampaignUpdate, authorization: str = Header(...)):
    politician_id = get_politician_id(authorization)

    data = {k: v for k, v in campaign.dict().items() if v is not None}

    result = supabase.table("campaigns")\
        .update(data)\
        .eq("id", campaign_id)\
        .eq("politician_id", politician_id)\
        .execute()
    return result.data[0]

# DELETE campaign
@router.delete("/{campaign_id}")
def delete_campaign(campaign_id: str, authorization: str = Header(...)):
    politician_id = get_politician_id(authorization)
    supabase.table("campaigns")\
        .delete()\
        .eq("id", campaign_id)\
        .eq("politician_id", politician_id)\
        .execute()
    return {"message": "Campaign deleted successfully"}

# GET campaign stats
@router.get("/{campaign_id}/stats")
def get_campaign_stats(campaign_id: str, authorization: str = Header(...)):
    politician_id = get_politician_id(authorization)
    result = supabase.table("campaigns")\
        .select("total_contacts, called, failed, busy, no_answer")\
        .eq("id", campaign_id)\
        .eq("politician_id", politician_id)\
        .single()\
        .execute()
    return result.data