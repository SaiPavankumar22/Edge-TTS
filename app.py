from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import edge_tts
import asyncio
import logging
import os
import time



app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_FOLDER = "responses"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


templates = Jinja2Templates(directory="templates")

class TextToSpeechRequest(BaseModel):
    text: str
    output_path: str = "responses/response.mp3"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

async def edge_tts_async(text, output_path, voice="en-US-JennyNeural"):
    logger.debug(f"Converting text to speech: {text[:100]}...")
    try:
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(output_path)
        logger.debug(f"Successfully saved audio to {output_path}")
    except Exception as e:
        logger.error(f"Error in text-to-speech conversion: {str(e)}")
        raise

async def text_to_speech(text, output_path="responses/response.mp3"):
    logger.debug("Starting text-to-speech conversion")
    try:
        await edge_tts_async(text, output_path)
        return output_path
    except Exception as e:
        logger.error(f"Error in text_to_speech: {str(e)}")
        raise


@app.post("/text_to_speech")
async def text_to_speech_route(request: TextToSpeechRequest):
    logger.info("Received text-to-speech request")
    try:
        text = request.text

        if not text:
            logger.error("No text provided")
            raise HTTPException(status_code=400, detail="No text provided")

        output_filename = f"response_{int(time.time())}.mp3"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        await text_to_speech(text, output_path)

        return FileResponse(output_path, media_type='audio/mpeg')
    except Exception as e:
        logger.error(f"Error processing text-to-speech request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
