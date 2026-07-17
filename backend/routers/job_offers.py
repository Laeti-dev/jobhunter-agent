from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.database import get_latest_cv
from utils.france_travail import france_travail
from utils.rag import cv_rag, analyze_offer, score_offers, suggest_alternative_roles

router = APIRouter(prefix="/jobs")


class SearchRequest(BaseModel):
    keywords: str
    region: str = "11"


class AnalyzeRequest(BaseModel):
    offer_id: str


class ScoreRequest(BaseModel):
    offers: list[dict]


@router.get("/regions")
def get_regions():
    """Return all available regions from France Travail's referentiel."""
    return france_travail.get_regions()


@router.get("/suggest-params")
def suggest_params():
    """Return pre-filled search params from the stored CV (no LLM — just target_role)."""
    cv = get_latest_cv()
    if cv is None:
        raise HTTPException(status_code=404, detail="Aucun CV trouvé.")
    return {"keywords": cv.target_role or "", "region": "11"}


@router.post("/search")
def search_offers(query: SearchRequest):
    """Search for job offers by job title and region."""
    offers = france_travail.search_offers(
        mots_cles=query.keywords,
        region=query.region,
    )
    return {"offers": offers, "total": len(offers)}


@router.get("/suggest-roles")
def suggest_roles(role: str):
    """Ask the LLM to suggest 3 job titles close to `role`, based on the stored CV."""
    cv = get_latest_cv()
    if cv is None:
        raise HTTPException(status_code=404, detail="Aucun CV trouvé.")
    try:
        roles = suggest_alternative_roles(cv, searched_role=role)
        return {"roles": roles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{offer_id}")
def get_offer(offer_id: str):
    """Return the full details of a specific job offer."""
    return france_travail.get_offer(offer_id)


@router.post("/score")
def score_job_offers(request: ScoreRequest):
    """Score and rank offers by semantic similarity against the stored CV and GitHub repos."""
    if not request.offers:
        return {"scored_offers": []}
    return {"scored_offers": score_offers(request.offers)}


@router.post("/analyze")
def analyze(request: AnalyzeRequest):
    """Analyze the match between the stored CV and a job offer using RAG."""
    cv = get_latest_cv()
    if cv is None:
        raise HTTPException(status_code=404, detail="Aucun CV trouvé.")

    offer = france_travail.get_offer(request.offer_id)
    cv_rag.index_cv(cv)
    chunks = cv_rag.retrieve(
        f"{offer.get('intitule', '')} {offer.get('description', '')[:500]}",
        n_results=3,
    )
    analysis = analyze_offer(offer, chunks)
    return {"analysis": analysis, "matched_sections": chunks}
