from fastapi import APIRouter, HTTPException, Header
from models import TemplateCreate, TemplateUpdate
from database import supabase
from services.tts import generate_and_upload_audio
from typing import Optional

router = APIRouter()

def get_politician_id(authorization: str) -> str:
    """Extract politician_id from auth token"""
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        return user.user.id
    except:
        raise HTTPException(status_code=401, detail="Unauthorized")

# GET all templates for logged-in politician
@router.get("/")
def get_templates(authorization: str = Header(...)):
    politician_id = get_politician_id(authorization)
    result = supabase.table("script_templates")\
        .select("*")\
        .eq("politician_id", politician_id)\
        .order("created_at", desc=True)\
        .execute()
    return result.data

# GET single template
@router.get("/{template_id}")
def get_template(template_id: str, authorization: str = Header(...)):
    politician_id = get_politician_id(authorization)
    result = supabase.table("script_templates")\
        .select("*")\
        .eq("id", template_id)\
        .eq("politician_id", politician_id)\
        .single()\
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Template not found")
    return result.data

# POST create new template
@router.post("/")
def create_template(template: TemplateCreate, authorization: str = Header(...)):
    politician_id = get_politician_id(authorization)
    
    data = {
        "politician_id": politician_id,
        "name": template.name,
        "script_kn": template.script_kn,
        "script_hi": template.script_hi,
    }

    result = supabase.table("script_templates").insert(data).execute()
    new_template = result.data[0]
    template_id = new_template["id"]

    # Generate audio if scripts provided
    if template.script_kn:
        url = generate_and_upload_audio(template.script_kn, "kn", template_id)
        supabase.table("script_templates")\
            .update({"audio_url_kn": url})\
            .eq("id", template_id)\
            .execute()
        new_template["audio_url_kn"] = url

    if template.script_hi:
        url = generate_and_upload_audio(template.script_hi, "hi", template_id)
        supabase.table("script_templates")\
            .update({"audio_url_hi": url})\
            .eq("id", template_id)\
            .execute()
        new_template["audio_url_hi"] = url

    return new_template

# PUT update template
@router.put("/{template_id}")
def update_template(template_id: str, template: TemplateUpdate, authorization: str = Header(...)):
    politician_id = get_politician_id(authorization)

    data = {k: v for k, v in template.dict().items() if v is not None}

    # Regenerate audio if scripts changed
    if "script_kn" in data:
        url = generate_and_upload_audio(data["script_kn"], "kn", template_id)
        data["audio_url_kn"] = url

    if "script_hi" in data:
        url = generate_and_upload_audio(data["script_hi"], "hi", template_id)
        data["audio_url_hi"] = url

    result = supabase.table("script_templates")\
        .update(data)\
        .eq("id", template_id)\
        .eq("politician_id", politician_id)\
        .execute()

    return result.data[0]

# DELETE template
@router.delete("/{template_id}")
def delete_template(template_id: str, authorization: str = Header(...)):
    politician_id = get_politician_id(authorization)
    supabase.table("script_templates")\
        .delete()\
        .eq("id", template_id)\
        .eq("politician_id", politician_id)\
        .execute()
    return {"message": "Template deleted successfully"}