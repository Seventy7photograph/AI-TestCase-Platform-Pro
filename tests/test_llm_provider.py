"""LLM Provider 单测：协议组装、错误映射、JSON 重试、降级策略。

全部使用 httpx.AsyncClient 替身，不发真实网络请求。
"""
from __future__ import annotations

import json

import httpx
import pytest

from app.core.config import Settings
from app.core.exceptions import LLMError, LLMNotConfiguredError, LLMResponseFormatError
from app.llm import openai_compatible
from app.llm.base import system, user
from app.llm.deepseek_provider import DeepSeekProvider
from app.llm.fake_provider import FakeProvider
from app.llm.factory import build_llm_provider
from app.llm.null_provider import NullProvider
from app.llm.prompts import build_requirement_messages, build_scenario_messages

MESSAGES = [system("你是测试架构师"), user("请输出 JSON")]


class _FakeResponse:
    def __init__(self, *, status_code: int = 200, payload: dict | None = None, text: str | None = None) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text if text is not None else json.dumps(payload or {}, ensure_ascii=False)

    def json(self) -> dict:
        if self._payload is None:
            raise ValueError("not json")
        return self._payload


class _FakeClient:
    def __init__(self, outcomes: list, captured: list) -> None:
        self.outcomes = outcomes
        self.captured = captured

    async def __aenter__(self) -> "_FakeClient":
        return self

    async def __aexit__(self, *exc) -> bool:
        return False

    async def post(self, url, json=None, headers=None):  # noqa: A002 - 对齐 httpx 签名
        self.captured.append({"url": url, "payload": json, "headers": headers})
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def patch_client(monkeypatch, outcomes: list) -> list:
    captured: list = []
    monkeypatch.setattr(
        openai_compatible.httpx, "AsyncClient", lambda **kwargs: _FakeClient(outcomes, captured)
    )
    return captured


def completion(content: str, *, model: str = "deepseek-chat") -> _FakeResponse:
    return _FakeResponse(
        payload={
            "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
        }
    )


def provider(**overrides) -> DeepSeekProvider:
    base = {"llm_provider": "deepseek", "llm_api_key": "test-key", "llm_base_url": "https://api.deepseek.com", "llm_model": "deepseek-chat", "llm_max_retries": 2}
    base.update(overrides)
    return DeepSeekProvider(Settings(**base))


async def test_complete_builds_openai_compatible_request(monkeypatch) -> None:
    captured = patch_client(monkeypatch, [completion('{"ok": true}')])
    response = await provider().complete(MESSAGES, json_mode=True, temperature=0.1, max_tokens=128)

    assert captured[0]["url"] == "https://api.deepseek.com/chat/completions"
    assert captured[0]["headers"]["Authorization"] == "Bearer test-key"
    assert captured[0]["payload"]["response_format"] == {"type": "json_object"}
    assert captured[0]["payload"]["temperature"] == 0.1
    assert captured[0]["payload"]["max_tokens"] == 128
    assert response.content == '{"ok": true}'
    assert response.usage["total_tokens"] == 20


async def test_http_error_maps_to_llm_error(monkeypatch) -> None:
    patch_client(monkeypatch, [_FakeResponse(status_code=401, payload={"error": "invalid key"})])
    with pytest.raises(LLMError) as excinfo:
        await provider().complete(MESSAGES)
    assert "401" in excinfo.value.message


async def test_timeout_maps_to_llm_error(monkeypatch) -> None:
    patch_client(monkeypatch, [httpx.TimeoutException("timeout")])
    with pytest.raises(LLMError) as excinfo:
        await provider().complete(MESSAGES)
    assert "超时" in excinfo.value.message


async def test_missing_choices_raises_format_error(monkeypatch) -> None:
    patch_client(monkeypatch, [_FakeResponse(payload={"model": "x"})])
    with pytest.raises(LLMResponseFormatError):
        await provider().complete(MESSAGES)


async def test_empty_content_raises_format_error(monkeypatch) -> None:
    patch_client(monkeypatch, [completion("   ")])
    with pytest.raises(LLMResponseFormatError):
        await provider().complete(MESSAGES)


async def test_complete_json_retries_after_invalid_output(monkeypatch) -> None:
    captured = patch_client(
        monkeypatch,
        [completion("抱歉，我无法输出 JSON。"), completion('{"items": [{"title": "注册"}]}')],
    )
    response = await provider().complete_json(MESSAGES)

    assert response.parsed == {"items": [{"title": "注册"}]}
    assert response.attempts == 2
    assert len(captured) == 2
    # 第二次调用应带上"修复 JSON"的追加消息
    assert any("JSON" in message["content"] for message in captured[1]["payload"]["messages"][-1:])


async def test_complete_json_raises_after_retries_exhausted(monkeypatch) -> None:
    patch_client(monkeypatch, [completion("no json here"), completion("still no json"), completion("nope")])
    with pytest.raises(LLMResponseFormatError) as excinfo:
        await provider(llm_max_retries=2).complete_json(MESSAGES)
    assert "3 次" in excinfo.value.message


async def test_complete_json_rejects_wrong_top_level_type(monkeypatch) -> None:
    patch_client(monkeypatch, [completion("[1,2,3]"), completion("[1,2,3]"), completion("[1,2,3]")])
    with pytest.raises(LLMResponseFormatError):
        await provider(llm_max_retries=1).complete_json(MESSAGES, expect=dict)


async def test_deepseek_default_base_url(monkeypatch) -> None:
    instance = DeepSeekProvider(Settings(llm_api_key="k", llm_base_url="", llm_model=""))
    assert instance.endpoint == "https://api.deepseek.com/chat/completions"
    assert instance.model == "deepseek-chat"


# --------------------------------------------------------------------------- #
# 降级与占位 Provider
# --------------------------------------------------------------------------- #
def test_factory_degrades_to_null_without_key() -> None:
    instance = build_llm_provider(Settings(llm_provider="deepseek", llm_api_key=""))
    assert isinstance(instance, NullProvider)
    assert instance.available is False
    assert "LLM_API_KEY" in instance.degraded_reason


def test_factory_returns_deepseek_with_key() -> None:
    instance = build_llm_provider(Settings(llm_provider="deepseek", llm_api_key="k"))
    assert isinstance(instance, DeepSeekProvider) and instance.available


def test_factory_supports_fake_provider() -> None:
    assert isinstance(build_llm_provider(Settings(llm_provider="fake")), FakeProvider)


def test_factory_unknown_provider_degrades() -> None:
    instance = build_llm_provider(Settings.model_construct(llm_provider="mystery", llm_api_key="k"))
    assert isinstance(instance, NullProvider)


async def test_null_provider_raises() -> None:
    instance = NullProvider(Settings(), reason="测试原因")
    with pytest.raises(LLMNotConfiguredError):
        await instance.complete(MESSAGES)
    with pytest.raises(LLMNotConfiguredError):
        await instance.complete_json(MESSAGES)
    assert await instance.health_check() is False


async def test_fake_provider_returns_task_specific_payload(settings) -> None:
    instance = FakeProvider(settings)
    response = await instance.complete_json(build_requirement_messages("测试需求", title="t", max_items=3))
    assert response.parsed["items"][0]["title"] == "用户注册"

    scenario = await instance.complete_json(
        build_scenario_messages({"id": "REQ-001"}, existing_titles=["a"], max_cases=3)
    )
    assert isinstance(scenario.parsed["cases"], list)

    unknown = await instance.complete_json([user("无任务标记")])
    assert unknown.parsed.get("_fake") is True