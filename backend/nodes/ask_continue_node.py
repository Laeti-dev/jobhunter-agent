from graphs.state import CVState
from sections import SECTIONS


def ask_continue_node(state: CVState) -> CVState:
    """Ask a fixed question about whether to add another item to the current section."""
    section = SECTIONS[state["section_index"]]
    article = section.get("article", "un(e)")
    is_first = not state["current_items"]

    if is_first and section.get("optional"):
        content = f"Avez-vous {article} {section['label']} à inclure dans votre CV ?"
    else:
        content = f"Voulez-vous ajouter {article} autre {section['label']} ?"

    question = {"role": "assistant", "content": content}

    return {
        "context_messages": state["context_messages"] + [question],
        "awaiting_continue": True,
    }
