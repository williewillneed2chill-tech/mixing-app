from fastapi import FastAPI
from pydub import AudioSegment
import requests
import uuid

app = FastAPI()

@app.post("/mix")
async def mix_beat(payload: dict):
    stems = payload.get("stems", [])
    output_format = payload.get("output_format", "wav")

    combined = None

    for stem in stems:
        url = stem["url"]
        response = requests.get(url)
        temp_file = f"/tmp/{uuid.uuid4()}.wav"

        with open(temp_file, "wb") as f:
            f.write(response.content)

        audio = AudioSegment.from_file(temp_file)

        if combined is None:
            combined = audio
        else:
            combined = combined.overlay(audio)

    out_file = f"/tmp/result.{output_format}"
    combined.export(out_file, format=output_format)

    return {
        "status": "complete",
        "message": "Mix complete (starter engine)",
        "result_url": "TEMP_URL"
    }
