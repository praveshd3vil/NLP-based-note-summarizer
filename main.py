import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio

import summarizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — loading summarization model")
    summarizer.load_model()
    logger.info("server is ready")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Note Summarizer API",
    description="Ai-note summarizer.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="The note text to summarize")


class SummarizeResponse(BaseModel):
    summary: str

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "model_loaded": summarizer.is_model_loaded(),
    }


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_note(payload: SummarizeRequest):
    text = payload.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text field cannot be empty.")

    if not summarizer.is_model_loaded():
        raise HTTPException(
            status_code=503,
            detail="Summarization model is still loading.",
        )

    try:
        loop = asyncio.get_event_loop()
        summary = await loop.run_in_executor(None, summarizer.summarize_text, text)
        return SummarizeResponse(summary=summary)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.exception("Summarization failed")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate summary. Please try again.",
        )
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
