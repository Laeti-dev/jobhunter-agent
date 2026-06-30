from fastapi import APIRouter, HTTPException
from utils.database import get_latest_cv
from utils.query_builder import build_query, FranceTravailQuery
from utils.france_travail import france_travail

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
    return {"offers": offers, "total": len(offers)}
