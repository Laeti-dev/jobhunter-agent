from litellm import completion
from graphs.state import CVState
from sections import SECTIONS
from prompts import build_question_prompt


def ask_in_section_node(state: CVState, model: str = "ollama/qwen2.5:7b") -> CVState:
    """Ask the next question for the current flat section (identity, skills, languages)."""
    section = SECTIONS[state["section_index"]]
    system_prompt = build_question_prompt(section["label"], section["instructions"], "SECTION_DONE")
    messages = [{"role": "system", "content": system_prompt}] + state["context_messages"]

    response = completion(
        model=model,
        messages=messages,
        temperature=0.2,
        stop=["### User:", "\nUser:", "\nUtilisateur:", "\n### "],
    )
    raw_content = response.choices[0].message.content
    visible = raw_content.replace("[SECTION_DONE]", "").strip()
    if not visible:
        raw_content = f"Parlez-moi de votre {section['label']}. {raw_content}"

    return {"context_messages": state["context_messages"] + [{"role": "assistant", "content": raw_content}]}
