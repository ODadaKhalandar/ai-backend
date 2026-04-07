from twilio.rest import Client
import os

def make_call(to: str, audio_url: str, contact_id: str, campaign_id: str) -> str:
    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )

    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

    call = client.calls.create(
        to=to,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        url=f"{backend_url}/twiml/{contact_id}?audio_url={audio_url}&campaign_id={campaign_id}",
        status_callback=f"{backend_url}/twiml/status",
        status_callback_method="POST"
    )

    return call.sid