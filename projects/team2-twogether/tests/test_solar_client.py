import json

from pydantic import BaseModel

from backend.app.llm.solar_client import SolarChatClient, _parse_json_content


class ExampleSchema(BaseModel):
    approved: bool


class FakeTransport:
    def __init__(self, content):
        self.content = content
        self.calls = []

    def __call__(self, url, headers, payload, timeout):
        self.calls.append((url, headers, payload, timeout))
        return {"choices": [{"message": {"content": self.content}}]}


def test_solar_client_calls_chat_completions_and_validates_schema(monkeypatch):
    monkeypatch.setenv("SOLAR_ANALYSIS_ENABLED", "true")
    transport = FakeTransport('{"approved": true}')
    client = SolarChatClient(api_key="test-key", post_json=transport)

    result = client.complete_json(
        system_prompt="Return JSON.",
        user_payload={"text": "hello"},
        schema=ExampleSchema,
    )

    assert result.approved is True
    url, headers, payload, _ = transport.calls[0]
    assert url == "https://api.upstage.ai/v1/chat/completions"
    assert headers["Authorization"] == "Bearer test-key"
    assert payload["model"] == "solar-pro3"
    user_message = json.loads(payload["messages"][1]["content"])
    assert user_message["text"] == "hello"
    assert "_response_schema" in user_message


def test_parse_json_content_accepts_markdown_fence():
    assert _parse_json_content('```json\n{"approved": false}\n```') == {
        "approved": False
    }
