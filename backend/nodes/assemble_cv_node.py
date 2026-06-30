import json
from litellm import completion
from pydantic import BaseModel
from graphs.state import CVState
from cv_model import CVProfile


class _Summary(BaseModel):
    summary: str


def _strip_markers(value: object) -> object:
    """Recursively strip internal markers from string values in collected_data."""
    markers = ["[SECTION_DONE]", "[ITEM_DONE]"]
    if isinstance(value, str):
        for marker in markers:
            value = value.replace(marker, "")
        return value.strip()
    if isinstance(value, list):
        return [_strip_markers(item) for item in value]
    if isinstance(value, dict):
        return {k: _strip_markers(v) for k, v in value.items()}
    return value


def assemble_cv_node(state: CVState, model: str = "ollama/qwen2.5:7b") -> CVState:
    """Build the final CVProfile from the structured data collected section by section."""
    data = _strip_markers(state["collected_data"])

    summary_messages = [
        {"role": "system", "content": (
            "Rédige un résumé professionnel concis (2 à 3 phrases) pour un CV, à la "
            "PREMIÈRE PERSONNE (je, j'ai, je maîtrise...), à partir de ces données "
            "structurées. N'invente aucune information absente des données."
        )},
        {"role": "user", "content": json.dumps(data, ensure_ascii=False)},
    ]
    response = completion(model=model, messages=summary_messages, response_format=_Summary, temperature=0.1)
    summary = json.loads(response.choices[0].message.content)["summary"]

    profile = CVProfile(
        name=data.get("name", ""),
        email=data.get("email", ""),
        phone=data.get("phone"),
        city=data.get("city"),
        target_role=data.get("target_role", ""),
        summary=summary,
        spoken_languages=data.get("spoken_languages", []),
        experiences=data.get("experiences", []),
        education=data.get("education", []),
        tech_skills=data.get("tech_skills", []),
        soft_skills=data.get("soft_skills", []),
        projects=data.get("projects", []),
    )

    closing_message = {
        "role": "assistant",
        "content": "Merci ! J'ai toutes les informations nécessaires, votre CV est généré.",
    }

    return {
        "context_messages": [closing_message],
        "cv_data": profile.model_dump_json(),
    }
