import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from graphs.cv_graph import cv_graph
from graphs.state import DEFAULT_CV_STATE
from database import get_latest_cv
from sections import SECTIONS

router = APIRouter(prefix="/cv")


class CVChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


@router.post("/chat")
async def cv_chat(request: CVChatRequest):
    """Receive a user message and advance the CV builder agent's session."""
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    snapshot = cv_graph.get_state(config)
    current_state = snapshot.values or DEFAULT_CV_STATE

    updated_context = current_state["context_messages"] + [{"role": "user", "content": request.message}]
    input_state = {**current_state, "context_messages": updated_context}

    result = cv_graph.invoke(input_state, config=config)

    raw_message = result["context_messages"][-1]["content"] if result["context_messages"] else ""
    last_message = raw_message.replace("[SECTION_DONE]", "").replace("[ITEM_DONE]", "").strip()
    cv_ready = result.get("cv_data") is not None
    section_index = result.get("section_index", 0)
    current_section = SECTIONS[section_index]["label"] if section_index < len(SECTIONS) else "Terminé"

    return {
        "response": last_message,
        "cv_ready": cv_ready,
        "thread_id": thread_id,
        "current_section": current_section,
    }


@router.get("/latest")
async def latest_cv():
    """Get the latest CV profile from the database."""
    cv = get_latest_cv()
    if cv is None:
        return {"cv": None}
    return {"cv": cv.model_dump()}
