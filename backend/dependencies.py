from dataclasses import dataclass

from fastapi import Header


@dataclass
class LLMConfig:
    model: str
    api_key: str | None


def get_llm_config(
    x_llm_model: str = Header(default="ollama/qwen2.5:7b"),
    x_llm_api_key: str | None = Header(default=None),
) -> LLMConfig:
    """
    Read the LLM model and API key from request headers.

    Defaults to the local Ollama model with no key, so existing calls
    (and the frontend, until it's updated) keep working unchanged.
    """
    return LLMConfig(model=x_llm_model, api_key=x_llm_api_key)
