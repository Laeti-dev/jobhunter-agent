import uuid
import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from pypdf import PdfReader
from io import BytesIO
from litellm import completion
from graphs.cv_graph import cv_graph, SESSION_STORE
from graphs.state import DEFAULT_CV_STATE
from utils.database import get_latest_cv, save_cv
from utils.rag import cv_rag
from cv_model import CVProfile
from sections import SECTIONS

router = APIRouter(prefix="/cv")


class CVChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


@router.post("/chat")
async def cv_chat(request: CVChatRequest):
    """Receive a user message and advance the CV builder agent's session."""
    thread_id = request.thread_id or str(uuid.uuid4())

    current_state = SESSION_STORE.get(thread_id, dict(DEFAULT_CV_STATE))
    updated_context = current_state["context_messages"] + [{"role": "user", "content": request.message}]
    input_state = {**current_state, "context_messages": updated_context}

    result = cv_graph.invoke(input_state)

    SESSION_STORE[thread_id] = result

    raw_message = result["context_messages"][-1]["content"] if result["context_messages"] else ""
    last_message = raw_message.replace("[SECTION_DONE]", "").replace("[ITEM_DONE]", "").strip()
    cv_ready = result.get("cv_data") is not None
    section_index = result.get("section_index", 0)
    current_section = SECTIONS[section_index]["label"] if section_index < len(SECTIONS) else "Terminé"

    if cv_ready:
        cv = get_latest_cv()
        if cv:
            cv_rag.index_cv(cv)

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


@router.post("/import")
async def import_cv(file: UploadFile = File(...)):
    """Extract text from a PDF, parse into CVProfile, save to SQLite and index in ChromaDB."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés.")

    content = await file.read()
    reader = PdfReader(BytesIO(content))
    raw_text = "\n".join(page.extract_text() or "" for page in reader.pages)

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Impossible d'extraire du texte de ce PDF.")

    messages = [
        {
            "role": "system",
            "content": (
                "Extrait les informations du CV fourni et retourne-les au format structuré. "
                "N'invente aucune information absente du document. "
                "Pour les champs non trouvés, utilise une chaîne vide ou une liste vide."
            ),
        },
        {"role": "user", "content": raw_text[:4000]},
    ]

    response = completion(
        model="ollama/qwen2.5:7b",
        messages=messages,
        response_format=CVProfile,
        temperature=0.1,
    )
    profile = CVProfile.model_validate_json(response.choices[0].message.content)

    save_cv(profile)
    cv_rag.index_cv(profile)  # deletes old vectors and re-indexes the new CV

    return {"cv": profile.model_dump(), "message": "CV importé et indexé avec succès."}
