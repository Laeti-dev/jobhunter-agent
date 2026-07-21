from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from nodes.analyze_cv_matches_node import analyze_cv_matches_node
from nodes.analyze_gh_matches_node import analyze_gh_matches_node
from nodes.assemble_cover_letter_node import assemble_cover_letter_node
from graphs.state import CoverLetterState


def dispatch_rag_agents(state: CoverLetterState) -> list[Send]:
    """Fan-out: explicitly send state to both RAG nodes so LangGraph waits for both."""
    return [
        Send("analyze_cv_matches", state),
        Send("analyze_gh_matches", state),
    ]


builder = StateGraph(CoverLetterState)

builder.add_node("analyze_cv_matches", analyze_cv_matches_node)
builder.add_node("analyze_gh_matches", analyze_gh_matches_node)
builder.add_node("assemble_cover_letter", assemble_cover_letter_node)

# fan-out via Send: LangGraph schedule both nodes explicitly, then waits for both
builder.add_conditional_edges(START, dispatch_rag_agents, ["analyze_cv_matches", "analyze_gh_matches"])

# fan-in: both branches converge here once their Annotated channels are populated
builder.add_edge("analyze_cv_matches", "assemble_cover_letter")
builder.add_edge("analyze_gh_matches", "assemble_cover_letter")

builder.add_edge("assemble_cover_letter", END)

cover_graph = builder.compile()
