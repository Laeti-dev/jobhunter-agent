from graphs.state import CoverLetterState
from utils.rag import cv_rag

def analyze_cv_matches_node(state: CoverLetterState) -> dict:
    offer = state["offer"]
    summary_text = " ".join(offer.get("summary", []))
    query = f"{offer.get('intitule', '')} {summary_text}"
    matches = cv_rag.retrieve(query)
    return {
        "cv_matches": matches,
    }
