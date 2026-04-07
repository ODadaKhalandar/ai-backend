from gtts import gTTS
from database import supabase
import tempfile
import os

def generate_and_upload_audio(text: str, language: str, template_id: str) -> str:
    """
    Generates audio from text using gTTS and uploads to Supabase Storage.
    Returns the public URL of the uploaded audio.
    """
    # Language code mapping
    lang_map = {
        "kn": "kn",  # Kannada
        "hi": "hi"   # Hindi
    }

    lang_code = lang_map.get(language, "kn")

    # Generate audio using gTTS
    tts = gTTS(text=text, lang=lang_code, slow=False)

    # Save to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp_path = tmp.name
        tts.save(tmp_path)

    # Upload to Supabase Storage
    file_name = f"{template_id}_{language}.mp3"

    with open(tmp_path, "rb") as f:
        supabase.storage.from_("audio").upload(
            path=file_name,
            file=f,
            file_options={"content-type": "audio/mpeg", "upsert": "true"}
        )

    # Cleanup temp file
    os.unlink(tmp_path)

    # Return public URL
    result = supabase.storage.from_("audio").get_public_url(file_name)
    return result