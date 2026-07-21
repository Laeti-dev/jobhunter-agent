from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.database import get_latest_cv
from utils.rag import cv_rag
from graphs.cover_graph import cover_graph

router = APIRouter(prefix="/cover")


class CoverRequest(BaseModel):
    intitule: str
    summary: list[str]


@router.post("/generate")
def generate_cover_letter(request: CoverRequest):
    """Run the cover letter multi-agent graph and return the generated letter."""
    cv = get_latest_cv()
    if cv is None:
        raise HTTPException(status_code=404, detail="Aucun CV trouvé.")
    cv_rag.index_cv(cv)

    result = cover_graph.invoke({
        "offer": {"intitule": request.intitule, "summary": request.summary},
        "cv_matches": [],
        "github_matches": [],
        "cover_letter": "",
    })

    return {"cover_letter": result.get("cover_letter", "")}
