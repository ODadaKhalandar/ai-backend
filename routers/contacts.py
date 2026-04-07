from fastapi import APIRouter, HTTPException, Header, UploadFile, File
from database import supabase
import csv
import io

router = APIRouter()

def get_politician_id(authorization: str) -> str:
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        return user.user.id
    except:
        raise HTTPException(status_code=401, detail="Unauthorized")

# GET all contacts for a campaign
@router.get("/{campaign_id}")
def get_contacts(campaign_id: str, authorization: str = Header(...)):
    get_politician_id(authorization)
    result = supabase.table("contacts")\
        .select("*")\
        .eq("campaign_id", campaign_id)\
        .order("created_at", desc=True)\
        .execute()
    return result.data

# POST upload CSV of contacts
@router.post("/{campaign_id}/upload")
async def upload_contacts(
    campaign_id: str,
    file: UploadFile = File(...),
    authorization: str = Header(...)
):
    get_politician_id(authorization)

    # Read CSV file
    contents = await file.read()
    decoded = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    all_contacts = []
    for row in reader:
        phone = row.get("phone", "").strip()
        if not phone:
            continue
        all_contacts.append({
            "campaign_id": campaign_id,
            "name": row.get("name", "").strip(),
            "phone": phone,
            "language": row.get("language", "kn").strip(),
            "status": "pending"
        })

    if not all_contacts:
        raise HTTPException(status_code=400, detail="No valid contacts found in CSV")

    # Insert in batches of 500 to avoid timeout
    BATCH_SIZE = 500
    total_inserted = 0

    for i in range(0, len(all_contacts), BATCH_SIZE):
        batch = all_contacts[i:i + BATCH_SIZE]
        supabase.table("contacts").insert(batch).execute()
        total_inserted += len(batch)

    # Update total_contacts count in campaign
    supabase.table("campaigns")\
        .update({"total_contacts": total_inserted})\
        .eq("id", campaign_id)\
        .execute()

    return {
        "message": f"{total_inserted} contacts uploaded successfully",
        "total": total_inserted,
        "batches": round(total_inserted / BATCH_SIZE)
    }

# DELETE all contacts for a campaign
@router.delete("/{campaign_id}")
def delete_contacts(campaign_id: str, authorization: str = Header(...)):
    get_politician_id(authorization)
    supabase.table("contacts")\
        .delete()\
        .eq("campaign_id", campaign_id)\
        .execute()
    return {"message": "All contacts deleted"}

# GET download contacts as CSV report
@router.get("/{campaign_id}/download")
def download_contacts(campaign_id: str, authorization: str = Header(...)):
    get_politician_id(authorization)
    result = supabase.table("contacts")\
        .select("*")\
        .eq("campaign_id", campaign_id)\
        .execute()

    contacts = result.data
    if not contacts:
        raise HTTPException(status_code=404, detail="No contacts found")

    # Build CSV string
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["name", "phone", "language", "status", "call_duration", "called_at"])
    writer.writeheader()
    for c in contacts:
        writer.writerow({
            "name": c.get("name", ""),
            "phone": c.get("phone", ""),
            "language": c.get("language", ""),
            "status": c.get("status", ""),
            "call_duration": c.get("call_duration", 0),
            "called_at": c.get("called_at", "")
        })

    from fastapi.responses import StreamingResponse
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=campaign_{campaign_id}_report.csv"}
    )