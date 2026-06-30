from graphs.state import CVState
from sections import SECTIONS


def ask_continue_node(state: CVState) -> CVState:
    """Ask a fixed question about whether to add another item to the current section."""
    section = SECTIONS[state["section_index"]]
    article = section.get("article", "un(e)")
    question = {
        "role": "assistant",
        "content": f"Voulez-vous ajouter {article} autre {section['label']} ?",
    }

    return {
        "context_messages": state["context_messages"] + [question],
        "awaiting_continue": True,
    }
