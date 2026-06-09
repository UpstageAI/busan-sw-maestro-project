from __future__ import annotations

import json
import os
import re
from typing import Any, Callable, TypeVar
from urllib import request

from pydantic import BaseModel

from backend.app.core.env import DEFAULT_ENV_PATH, load_dotenv


DEFAULT_SOLAR_BASE_URL = "https://api.upstage.ai/v1"
DEFAULT_SOLAR_MODEL = "solar-pro3"

PostJson = Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]]
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class SolarChatClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
        post_json: PostJson | None = None,
    ):
        self.api_key = api_key or os.getenv("UPSTAGE_API_KEY", "")
        self.base_url = (base_url or os.getenv("SOLAR_BASE_URL", DEFAULT_SOLAR_BASE_URL)).rstrip("/")
        self.model = model or os.getenv("SOLAR_MODEL", DEFAULT_SOLAR_MODEL)
        self.timeout = timeout or _env_int("SOLAR_TIMEOUT", 20)
        self._post_json = post_json or _post_json

    @classmethod
    def from_env(cls, env_path=DEFAULT_ENV_PATH) -> "SolarChatClient":
        load_dotenv(env_path)
        return cls()

    @property
    def is_configured(self) -> bool:
        enabled = os.getenv("SOLAR_ANALYSIS_ENABLED", "true").strip().lower()
        return bool(self.api_key) and enabled not in {"0", "false", "no", "off"}

    def complete_json(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, Any],
        schema: type[SchemaT],
    ) -> SchemaT:
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY is required for Solar chat requests.")

        response = self._post_json(
            f"{self.base_url}/chat/completions",
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                **user_payload,
                                "_response_schema": schema.model_json_schema(),
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
                "temperature": 0,
            },
            self.timeout,
        )
        content = response["choices"][0]["message"]["content"]
        return schema.model_validate(_parse_json_content(content))


def _parse_json_content(content: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(content, dict):
        return content

    text = str(content).strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(text[start : end + 1])

    if not isinstance(parsed, dict):
        raise ValueError("Solar response must be a JSON object.")
    return parsed


def _post_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(url, data=body, headers=headers, method="POST")
    with request.urlopen(req, timeout=timeout) as response:
        response_body = response.read().decode("utf-8")
    return json.loads(response_body)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default
