from typing import TypedDict, List, Annotated
import operator


class BaseState(TypedDict):
    """Shared state across all LangGraph graphs in this project."""
    messages: List[dict]


class CVState(TypedDict):
    section_index: int
    context_messages: List[dict]
    current_items: List[dict]
    collected_data: dict
    awaiting_continue: bool
    wants_more_items: bool
    cv_data: str | None
    cv_id: int | None


DEFAULT_CV_STATE: CVState = {
    "section_index": 0,
    "context_messages": [],
    "current_items": [],
    "collected_data": {},
    "awaiting_continue": False,
    "wants_more_items": False,
    "cv_data": None,
    "cv_id": None,
}

class CoverLetterState(TypedDict):
    offer: dict
    cv_matches: Annotated[list, operator.add]      # reducer: accumulates results from parallel branches
    github_matches: Annotated[list, operator.add]  # reducer: accumulates results from parallel branches
    cover_letter: str
