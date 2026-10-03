"""LLM Provider 抽象基类。

约束：业务代码只依赖本模块的抽象，不感知具体厂商。
内置能力：
  - complete()      单轮补全
  - complete_json() JSON 模式 + 解析失败自动修复重试（抵抗模型输出抖动）
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any

from app.core.config import Settings, get_settings
from app.core.exceptions import LLMError, LLMResponseFormatError
from app.core.logging import get_logger
from app.core.utils import dump_json, extract_json, truncate

logger = get_logger(__name__)

JSON_REPAIR_INSTRUCTION = (
    "上一次回复无法解析为 JSON。请只输出一个合法 JSON 对象（不要 Markdown 代码块、"
    "不要解释文字、不要尾随逗号），字段名使用双引号。"
)


@dataclass(slots=True)
class LLMMessage:
    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


def system(content: str) -> LLMMessage:
    return LLMMessage(role="system", content=content)


def user(content: str) -> LLMMessage:
    return LLMMessage(role="user", content=content)


def assistant(content: str) -> LLMMessage:
    return LLMMessage(role="assistant", content=content)


@dataclass(slots=True)
class LLMResponse:
    """一次补全的结果：正文 + 可观测元信息。"""

    content: str
    model: str = ""
    usage: dict[str, Any] = field(default_factory=dict)
    elapsed_ms: int = 0
    attempts: int = 1
    parsed: Any = None
    raw: dict[str, Any] = field(default_factory=dict)


class LLMProvider(abc.ABC):
    """所有大模型适配器的基类。"""

    name: str = "base"
    supports_json_mode: bool = True

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.degraded_reason: str = ""

    # ------------------------------------------------------------------ #
    # 由子类实现
    # ------------------------------------------------------------------ #
    @property
    @abc.abstractmethod
    def available(self) -> bool:
        """是否具备真实调用能力（False 时业务层直接走规则引擎）。"""

    @abc.abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """执行一次对话补全。"""

    # ------------------------------------------------------------------ #
    # 通用能力
    # ------------------------------------------------------------------ #
    @property
    def model(self) -> str:
        return self.settings.llm_model

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "model": self.model,
            "available": self.available,
            "degraded_reason": self.degraded_reason,
        }

    async def complete_json(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        retries: int | None = None,
        expect: type | tuple[type, ...] = (dict, list),
    ) -> LLMResponse:
        """调用并解析 JSON；失败时追加修复指令重试。

        :raises LLMError: 网络/接口层错误
        :raises LLMResponseFormatError: 多次重试后仍非合法 JSON
        """
        max_retries = self.settings.llm_max_retries if retries is None else retries
        working = list(messages)
        last_error: Exception | None = None
        last_content = ""

        for attempt in range(1, max_retries + 2):
            response = await self.complete(
                working,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=True,
            )
            response.attempts = attempt
            last_content = response.content
            try:
                parsed = extract_json(response.content)
            except ValueError as exc:
                last_error = exc
                logger.warning("LLM 第 %s 次输出无法解析为 JSON：%s", attempt, exc)
                working = [
                    *messages,
                    assistant(truncate(response.content, 1200)),
                    user(JSON_REPAIR_INSTRUCTION),
                ]
                continue

            if not isinstance(parsed, expect):
                last_error = LLMResponseFormatError(
                    f"期望顶层为 {expect}，实际为 {type(parsed).__name__}",
                    detail={"content_preview": truncate(response.content, 500)},
                )
                working = [*messages, assistant(truncate(response.content, 1200)), user(JSON_REPAIR_INSTRUCTION)]
                continue

            response.parsed = parsed
            return response

        raise LLMResponseFormatError(
            f"模型连续 {max_retries + 1} 次未返回合法 JSON：{last_error}",
            detail={"content_preview": truncate(last_content, 800)},
        )

    async def aclose(self) -> None:  # pragma: no cover - 默认无资源可释放
        """释放底层连接资源（如 HTTP 会话）。"""
        return None

    async def health_check(self) -> bool:
        """轻量连通性检查，默认实现为一次极小请求。"""
        if not self.available:
            return False
        try:
            await self.complete([user("ping")], max_tokens=8, temperature=0.0)
            return True
        except LLMError:
            return False


def build_json_preview(data: Any, limit: int = 4000) -> str:
    """截断超长 JSON，控制 Prompt 体积。"""
    return truncate(dump_json(data, indent=None), limit)