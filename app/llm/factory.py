"""LLM Provider 工厂 + 注册表（依赖注入入口）。

降级策略（保证"没有 API Key 也能端到端跑通"）：
  显式 fake           -> FakeProvider
  未配置 API Key      -> NullProvider（业务层走纯规则引擎）
  配置齐全            -> 对应真实 Provider
"""
from __future__ import annotations

from functools import lru_cache
from typing import Callable

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.registry import Registry
from app.llm.base import LLMProvider
from app.llm.deepseek_provider import DeepSeekProvider
from app.llm.fake_provider import FakeProvider
from app.llm.null_provider import NullProvider
from app.llm.openai_compatible import OpenAICompatibleProvider

logger = get_logger(__name__)

# V3.0 扩展点：注册新的 Provider 只需一行
PROVIDER_REGISTRY: Registry[Callable[[Settings], LLMProvider]] = Registry("LLM Provider")

PROVIDER_REGISTRY.register("deepseek", lambda settings: DeepSeekProvider(settings))
PROVIDER_REGISTRY.register("openai_compatible", lambda settings: OpenAICompatibleProvider(settings))
PROVIDER_REGISTRY.register("fake", lambda settings: FakeProvider(settings))

_PROVIDERS_REQUIRING_KEY = {"deepseek", "openai_compatible"}


def build_llm_provider(settings: Settings | None = None, *, provider_name: str | None = None) -> LLMProvider:
    """按配置构建 Provider，必要时自动降级为 NullProvider。"""
    settings = settings or get_settings()
    name = (provider_name or settings.llm_provider or "deepseek").strip().lower()

    builder = PROVIDER_REGISTRY.try_get(name)
    if builder is None:
        logger.warning("未知的 LLM_PROVIDER=%s，降级为纯规则引擎", name)
        return NullProvider(settings, reason=f"未知的 LLM_PROVIDER：{name}")

    if name in _PROVIDERS_REQUIRING_KEY and not settings.llm_api_key.strip():
        reason = (
            f"未配置 LLM_API_KEY，已自动降级为纯规则引擎（provider={name}）。"
            "如需启用大模型，请在 .env 中填写 LLM_API_KEY。"
        )
        logger.warning(reason)
        return NullProvider(settings, reason=reason)

    provider = builder(settings)
    logger.info("LLM Provider 就绪：%s (%s)", provider.name, provider.model)
    return provider


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    """全局单例 Provider（依赖注入用）。"""
    return build_llm_provider(get_settings())


def reset_llm_provider_cache() -> None:
    get_llm_provider.cache_clear()