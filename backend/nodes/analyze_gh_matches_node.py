from graphs.state import CoverLetterState
from utils.rag import github_rag

def analyze_gh_matches_node(state: CoverLetterState) -> dict:
    offer = state["offer"]
    summary_text = " ".join(offer.get("summary", []))
    query = f"{offer.get('intitule', '')} {summary_text}"
    matches = github_rag.retrieve(query)
    return {
        "github_matches": matches,
    }
