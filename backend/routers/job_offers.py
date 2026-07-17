from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.database import get_latest_cv
from utils.france_travail import france_travail
from utils.rag import cv_rag, analyze_offer, score_offers, suggest_alternative_roles, summarize_offer, enrich_offer_detail

router = APIRouter(prefix="/jobs")


class SearchRequest(BaseModel):
    keywords: str
    region: str = "11"
    type_contrat: str | None = None   # CDI, CDD, STAGE — None = toutes
    experience: str | None = None     # "1" débutant, "2" junior, "3" confirmé — None = toutes


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
    """Search for job offers by job title, region, contract type, and experience level."""
    alternance = query.type_contrat == "ALTERNANCE"
    type_contrat = query.type_contrat if not alternance else None
    mots_cles = query.keywords
    if query.type_contrat == "STAGE":
        mots_cles = f"{mots_cles} stage"
        type_contrat = "CDD"

    offers = france_travail.search_offers(
        mots_cles=mots_cles,
        region=query.region,
        experience=query.experience,
        type_contrat=type_contrat,
        alternance=alternance,
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


@router.get("/{offer_id}/enrich")
def enrich_offer(offer_id: str):
    """
    Fetch full offer detail, then return:
    - a 3-bullet LLM summary
    - matched_skills (CV skills found in offer)
    - missing_skills (tech skills required but absent from CV)
    - the raw description
    """
    cv = get_latest_cv()
    cv_skills = cv.tech_skills or [] if cv else []

    offer_detail = france_travail.get_offer(offer_id)
    description = offer_detail.get("description", "")

    summary = summarize_offer(description)
    skill_tags = enrich_offer_detail(offer_detail, cv_skills)

    return {
        "summary": summary,
        "matched_skills": skill_tags["matched_skills"],
        "missing_skills": skill_tags["missing_skills"],
        "description": description,
    }


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
