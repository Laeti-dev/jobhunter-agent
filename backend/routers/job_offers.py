from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.database import get_latest_cv
from utils.query_builder import build_query, FranceTravailQuery
from utils.france_travail import france_travail
from utils.rag import cv_rag, analyze_offer

router = APIRouter(prefix="/jobs")


@router.get("/suggest-params")
def suggest_params():
    """Read the latest CV and suggest optimal France Travail search parameters."""
    cv = get_latest_cv()
    if cv is None:
        raise HTTPException(status_code=404, detail="Aucun CV trouvé. Créez-en un via le CV Builder.")
    query = build_query(cv)
    return {"query": query.model_dump()}


@router.post("/search")
def search_offers(query: FranceTravailQuery):
    """Search for job offers using the given parameters."""
    offers = france_travail.search_offers(
        mots_cles=query.keywords,
        region=query.region,
        experience=query.experience,
        niveau_formation=query.education_level,
    )
    for offer in offers:
        print(f"[OFFER] {offer.get('id')} — {offer.get('intitule')}")
    return {"offers": offers, "total": len(offers)}

@router.get("/{offer_id}")
def get_offer(offer_id: str):
    """Return the details of a specific job offer."""
    return france_travail.get_offer(offer_id)


class AnalyzeRequest(BaseModel):
    offer_id: str


@router.post("/analyze")
def analyze(request: AnalyzeRequest):
    """Analyze the match between the stored CV and a specific job offer using RAG."""
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

