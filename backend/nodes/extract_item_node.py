import json
from litellm import completion
from graphs.state import CVState
from sections import SECTIONS
from prompts import build_extraction_prompt
from nodes.extract_section_node import _clean


def extract_item_node(state: CVState, model: str = "ollama/qwen2.5:7b") -> CVState:
    """Extract structured data for the current item, append it, and clear the short context."""
    section = SECTIONS[state["section_index"]]
    messages = _clean(state["context_messages"]) + [build_extraction_prompt(section["label"])]

    response = completion(
        model=model,
        messages=messages,
        response_format=section["item_model"],
        temperature=0.1,
    )
    item_data = json.loads(response.choices[0].message.content)

    return {
        "current_items": state["current_items"] + [item_data],
        "context_messages": [],
    }
