from fastapi import FastAPI, HTTPException
from pydub import AudioSegment
import requests
import io

app = FastAPI()

def download_bytes(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, allow_redirects=True, timeout=45)
    r.raise_for_status()
    return r.content, r.headers.get("content-type", "")

def guess_format(content_type: str, url: str) -> str:
    ct = (content_type or "").lower()
    if "wav" in ct or url.lower().endswith(".wav"):
        return "wav"
    if "mpeg" in ct or "mp3" in ct or url.lower().endswith(".mp3"):
        return "mp3"
    if "ogg" in ct or url.lower().endswith(".ogg"):
        return "ogg"
    if "flac" in ct or url.lower().endswith(".flac"):
        return "flac"
    return "wav"

@app.post("/mix")
async def mix_beat(payload: dict):
    stems = payload.get("stems", [])
    output_format = payload.get("output_format", "wav")

    if not stems:
        raise HTTPException(status_code=422, detail="stems is required")

    combined = None

    for stem in stems:
        url = stem.get("url")
        if not url:
            raise HTTPException(status_code=422, detail="Each stem needs a url")

        data, content_type = download_bytes(url)

        # block HTML pages pretending to be files
        head = data[:300].lower()
        if head.startswith(b"<!doctype html") or b"<html" in head:
            raise HTTPException(status_code=400, detail=f"URL did not return audio (got HTML). content-type={content_type}")

        fmt = guess_format(content_type, url)

        try:
            audio = AudioSegment.from_file(io.BytesIO(data), format=fmt)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not decode audio. content-type={content_type}, format={fmt}, error={str(e)}")

        combined = audio if combined is None else combined.overlay(audio)

    out = io.BytesIO()
    combined.export(out, format=output_format)
    out.seek(0)

       out = io.BytesIO()
    combined.export(out, format=output_format)
    out.seek(0)

    filename = f"mix_{uuid.uuid4()}.{output_format}"
    media_type = "audio/wav" if output_format == "wav" else "audio/mpeg"

    return StreamingResponse(
        out,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

