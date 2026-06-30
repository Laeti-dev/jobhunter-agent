from graphs.state import CVState
from sections import SECTIONS

NEGATIVE_KEYWORDS = ["non", "no", "c'est tout", "rien d'autre", "pas d'autre"]
AFFIRMATIVE_KEYWORDS = ["oui", "yes", "encore", "ajouter"]


def is_affirmative(text: str) -> bool:
    """Classify a yes/no reply with simple keyword matching (deterministic, no LLM call)."""
    text = text.lower()
    if any(keyword in text for keyword in NEGATIVE_KEYWORDS):
        return False
    return any(keyword in text for keyword in AFFIRMATIVE_KEYWORDS)


def handle_continue_answer_node(state: CVState) -> CVState:
    """Decide whether to gather another item or move on to the next section."""
    last_user_message = state["context_messages"][-1]["content"]
    wants_more = is_affirmative(last_user_message)

    if wants_more:
        return {
            "context_messages": [],
            "awaiting_continue": False,
            "wants_more_items": True,
        }

    section = SECTIONS[state["section_index"]]
    updated_collected = {**state["collected_data"], section["key"]: state["current_items"]}

    return {
        "context_messages": [],
        "current_items": [],
        "collected_data": updated_collected,
        "section_index": state["section_index"] + 1,
        "awaiting_continue": False,
        "wants_more_items": False,
    }
