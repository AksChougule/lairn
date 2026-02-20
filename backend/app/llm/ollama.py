import json
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import settings

T = TypeVar("T", bound=BaseModel)


class OllamaClient:
    def __init__(self) -> None:
        self._client = httpx.Client(
            base_url=settings.ollama_base_url.rstrip("/"),
            timeout=settings.ollama_timeout_seconds,
        )

    def check_health(self) -> tuple[bool, str]:
        try:
            response = self._client.get("/api/tags")
            response.raise_for_status()
            payload = response.json()
            models = payload.get("models", [])
            installed_names = [model.get("name", "") for model in models if isinstance(model, dict)]
            model_is_available = settings.ollama_model in installed_names
            return model_is_available, settings.ollama_model
        except Exception:
            return False, settings.ollama_model

    def generate_json(self, *, prompt: str, response_model: type[T], max_retries: int = 2) -> T | None:
        for _ in range(max_retries + 1):
            try:
                response = self._client.post(
                    "/api/generate",
                    json={
                        "model": settings.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                    },
                )
                response.raise_for_status()
                payload: dict[str, Any] = response.json()
                raw_response = payload.get("response", "{}")
                parsed = self._parse_json_response(raw_response)
                return response_model.model_validate(parsed)
            except (httpx.HTTPError, json.JSONDecodeError, ValidationError, ValueError):
                continue
        return None

    @staticmethod
    def _parse_json_response(raw_response: Any) -> Any:
        if isinstance(raw_response, (dict, list)):
            return raw_response
        text = str(raw_response).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise
            candidate = text[start : end + 1]
            return json.loads(candidate)


ollama_client = OllamaClient()
