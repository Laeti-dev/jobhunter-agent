import json
import re
from typing import Optional, Union

import litellm
from pydantic import BaseModel
from deepeval.models import DeepEvalBaseLLM


class OllamaJudge(DeepEvalBaseLLM):
    """DeepEval judge backed by a local Ollama model via LiteLLM.

    Ollama runs locally and avoids cloud API restrictions. qwen2.5:7b is
    already used by this project for CV analysis, so no extra setup needed.
    """

    OLLAMA_MODEL = "ollama/qwen2.5:7b"

    def load_model(self) -> str:
        return self.OLLAMA_MODEL

    def _complete(self, prompt: str) -> str:
        response = litellm.completion(
            model=self.OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1024,
        )
        return response.choices[0].message.content

    def generate(
        self, prompt: str, schema: Optional[type[BaseModel]] = None
    ) -> Union[str, BaseModel]:
        # When DeepEval needs structured output, we embed the JSON schema in
        # the prompt — Ollama models don't support native function calling.
        if schema is not None:
            schema_str = json.dumps(schema.model_json_schema(), indent=2)
            prompt = (
                f"{prompt}\n\n"
                f"Return ONLY a valid JSON object matching this schema:\n{schema_str}"
            )

        raw_output = self._complete(prompt)

        if schema is None:
            return raw_output

        json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        raw_json = json_match.group() if json_match else raw_output
        return schema(**json.loads(raw_json))

    async def a_generate(
        self, prompt: str, schema: Optional[type[BaseModel]] = None
    ) -> Union[str, BaseModel]:
        return self.generate(prompt, schema)

    def get_model_name(self) -> str:
        return "qwen2.5:7b (Ollama local)"
