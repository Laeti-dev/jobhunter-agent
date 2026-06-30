from litellm import completion
from graphs.state import CVState
from sections import SECTIONS
from prompts import build_question_prompt


def ask_in_item_node(state: CVState, model: str = "ollama/qwen2.5:7b") -> CVState:
    """Ask the next question about the current item within a list-type section."""
    section = SECTIONS[state["section_index"]]
    label = f"UN(E) SEUL(E) {section['label']}"
    system_prompt = build_question_prompt(label, section["instructions"], "ITEM_DONE")
    messages = [{"role": "system", "content": system_prompt}] + state["context_messages"]

    response = completion(
        model=model,
        messages=messages,
        temperature=0.2,
        stop=["### User:", "\nUser:", "\nUtilisateur:", "\n### "],
    )
    assistant_message = {"role": "assistant", "content": response.choices[0].message.content}

    return {"context_messages": state["context_messages"] + [assistant_message]}
