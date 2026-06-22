from typing import TypedDict, List


class BaseState(TypedDict):
    """Shared state across all LangGraph graphs in this project."""
    messages: List[dict]


class CVState(BaseState):
    cv_data: str | None
