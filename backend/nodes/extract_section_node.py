import json
from litellm import completion
from graphs.state import CVState
from sections import SECTIONS
from prompts import build_extraction_prompt

MARKERS = ["[SECTION_DONE]", "[ITEM_DONE]"]


def _clean(messages: list[dict]) -> list[dict]:
    """Strip LangGraph internal markers from message content before sending to the LLM."""
    cleaned = []
    for msg in messages:
        content = msg["content"]
        for marker in MARKERS:
            content = content.replace(marker, "")
        cleaned.append({**msg, "content": content.strip()})
    return cleaned


def extract_section_node(state: CVState, model: str = "ollama/qwen2.5:7b") -> CVState:
    """Extract structured data for the current flat section and move to the next section."""
    section = SECTIONS[state["section_index"]]
    messages = _clean(state["context_messages"]) + [build_extraction_prompt(section["label"])]

    response = completion(
        model=model,
        messages=messages,
        response_format=section["model"],
        temperature=0.1,
    )
    section_data = json.loads(response.choices[0].message.content)

    return {
        "collected_data": {**state["collected_data"], **section_data},
        "section_index": state["section_index"] + 1,
        "context_messages": [],
    }
