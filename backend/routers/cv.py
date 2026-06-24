from fastapi import APIRouter
from pydantic import BaseModel
from graphs.cv_graph import cv_graph
from database import get_latest_cv

router = APIRouter(prefix="/cv")


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@router.post("/chat")
async def cv_chat(request: ChatRequest):
    """Receive a user message and return the CV builder agent's response."""
    messages = request.history + [{"role": "user", "content": request.message}]
    result = cv_graph.invoke({"messages": messages})
    last_message = result["messages"][-1]["content"]
    cv_ready = "[CV_READY]" in last_message
    return {
        "response": last_message.replace("[CV_READY]", "").strip(),
        "cv_ready": cv_ready,
    }


@router.get("/latest")
async def latest_cv():
    """Get the latest CV profile from the database."""
    cv = get_latest_cv()
    if cv is None:
        return {"cv": None}
    return {"cv": cv.model_dump()}
