"""大模型运行时配置接口。

GET    /llm/config       读取当前生效配置（Key 仅回显掩码 + 是否已配置）
PUT    /llm/config       保存界面覆盖配置（写 storage/data/llm_config.json，不重启即生效）
DELETE /llm/config       清除界面覆盖，恢复 .env 基线
POST   /llm/config/test  用当前配置或未保存的表单值做一次真实连通性测试
GET    /llm/models       拉取候选模型（远端 /models，失败回退内置目录）
"""
from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter

from app.api.deps import SettingsDep
from app.core.config import Settings, get_settings
from app.core.exceptions import LLMError
from app.core.logging import get_logger
from app.core.utils import truncate
from app.llm.base import user
from app.llm.catalog import provider_option, provider_options
from app.llm.factory import (
    build_llm_provider,
    get_effective_settings,
    get_llm_provider,
    get_runtime_config_store,
    reset_llm_provider_cache,
)
from app.llm.runtime_config import mask_api_key
from app.schemas.api import ApiResponse, ok
from app.schemas.llm import (
    LLMConfigInfo,
    LLMConfigUpdate,
    LLMModelList,
    LLMModelOption,
    LLMProviderOption,
    LLMTestRequest,
    LLMTestResult,
)

router = APIRouter(tags=["大模型配置"])

logger = get_logger(__name__)

_ENV_BASELINE_FIELDS = ("llm_provider", "llm_model", "llm_base_url", "llm_timeout",
                        "llm_max_retries", "llm_temperature", "llm_max_tokens")


def _baseline_defaults() -> dict[str, Any]:
    """返回 .env 基线的可回显项（不含明文 Key）。"""
    base = get_settings()
    defaults: dict[str, Any] = {key: getattr(base, key) for key in _ENV_BASELINE_FIELDS}
    defaults["api_key_configured"] = bool(base.llm_api_key.strip())
    return defaults


def _to_info(settings: Settings, provider: Any) -> LLMConfigInfo:
    overrides = get_runtime_config_store().read()
    return LLMConfigInfo(
        provider=settings.llm_provider,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        api_key_configured=bool(settings.llm_api_key.strip()),
        api_key_masked=mask_api_key(settings.llm_api_key),
        timeout=settings.llm_timeout,
        max_retries=settings.llm_max_retries,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        available=provider.available,
        degraded_reason=provider.degraded_reason,
        source="runtime" if overrides else "env",
        overridden_fields=sorted(overrides.keys()),
        env_defaults=_baseline_defaults(),
        providers=[LLMProviderOption(**item) for item in provider_options()],
    )


@router.get("/llm/config", response_model=ApiResponse[LLMConfigInfo], summary="读取大模型配置")
async def get_llm_config(settings: SettingsDep) -> dict:
    return ok(_to_info(get_effective_settings(), get_llm_provider()))


@router.put("/llm/config", response_model=ApiResponse[LLMConfigInfo], summary="保存大模型配置")
async def update_llm_config(payload: LLMConfigUpdate) -> dict:
    patch = {
        "llm_provider": payload.provider,
        "llm_model": payload.model,
        "llm_base_url": payload.base_url,
        "llm_api_key": payload.api_key,
        "llm_timeout": payload.timeout,
        "llm_max_retries": payload.max_retries,
        "llm_temperature": payload.temperature,
        "llm_max_tokens": payload.max_tokens,
    }
    get_runtime_config_store().save(patch)
    reset_llm_provider_cache()
    provider = get_llm_provider()
    logger.info("已更新运行时 LLM 配置：provider=%s model=%s", provider.name, provider.model)
    return ok(_to_info(get_effective_settings(), provider), message="大模型配置已保存。")


@router.delete("/llm/config", response_model=ApiResponse[LLMConfigInfo], summary="恢复 .env 配置")
async def reset_llm_config() -> dict:
    removed = get_runtime_config_store().clear()
    reset_llm_provider_cache()
    provider = get_llm_provider()
    message = "已恢复 .env 配置。" if removed else "当前没有界面覆盖配置，仍使用 .env 基线。"
    return ok(_to_info(get_effective_settings(), provider), message=message)


def _candidate_settings(payload: LLMTestRequest | None) -> Settings:
    """未保存表单值优先，其次已保存覆盖，最后 .env 基线。"""
    base = get_settings()
    overrides = dict(get_runtime_config_store().read())
    if payload is not None:
        mapping = {
            "llm_provider": payload.provider,
            "llm_model": payload.model,
            "llm_base_url": payload.base_url,
            "llm_api_key": payload.api_key,
            "llm_timeout": payload.timeout,
            "llm_temperature": payload.temperature,
            "llm_max_tokens": payload.max_tokens,
        }
        for key, value in mapping.items():
            if value is not None:
                overrides[key] = value
    return base.with_llm_overrides(overrides) if overrides else base


@router.post("/llm/config/test", response_model=ApiResponse[LLMTestResult], summary="测试大模型连通性")
async def test_llm_config(payload: LLMTestRequest | None = None) -> dict:
    settings = _candidate_settings(payload)
    provider = build_llm_provider(settings)
    if not provider.available:
        result = LLMTestResult(
            ok=False,
            provider=provider.name,
            model=provider.model,
            message=provider.degraded_reason or "当前配置不可用，请检查 API Key 与端点地址。",
        )
        return ok(result)
    try:
        response = await provider.complete(
            [user("请只回复两个字：连接成功")], max_tokens=16, temperature=0.0
        )
    except LLMError as exc:
        logger.warning("LLM 连通性测试失败：%s", exc.message)
        result = LLMTestResult(
            ok=False,
            provider=provider.name,
            model=provider.model,
            message=exc.message,
        )
        return ok(result)
    result = LLMTestResult(
        ok=True,
        provider=provider.name,
        model=response.model or provider.model,
        elapsed_ms=response.elapsed_ms,
        message="连接成功。",
        reply=truncate(response.content.strip(), 80),
    )
    return ok(result, message="大模型连接正常。")


@router.get("/llm/models", response_model=ApiResponse[LLMModelList], summary="获取候选模型列表")
async def list_llm_models(settings: SettingsDep, provider: str | None = None) -> dict:
    effective = get_effective_settings()
    name = (provider or effective.llm_provider or "deepseek").strip().lower()
    option = provider_option(name) or {}
    builtin = [
        LLMModelOption(**item) for item in option.get("models", [])
    ]

    base_url = (effective.llm_base_url or option.get("default_base_url") or "").rstrip("/")
    api_key = effective.llm_api_key.strip()
    if not base_url or not api_key or name in {"fake", "none"}:
        return ok(LLMModelList(source="builtin", models=builtin))

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=8.0), follow_redirects=True) as client:
            response = await client.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("拉取远端模型列表失败，回退内置目录：%s", exc)
        return ok(
            LLMModelList(source="builtin", message=f"拉取远端模型失败，已回退内置列表：{exc}", models=builtin)
        )

    items = payload.get("data") if isinstance(payload, dict) else None
    models: list[LLMModelOption] = []
    if isinstance(items, list):
        for item in items:
            value = str(item.get("id", "")).strip() if isinstance(item, dict) else ""
            if value:
                models.append(LLMModelOption(value=value, label=value, base_url=base_url))
    models.sort(key=lambda item: item.value)
    if not models:
        return ok(LLMModelList(source="builtin", message="远端未返回模型，已回退内置列表。", models=builtin))
    return ok(LLMModelList(source="remote", models=models))
