"""DeepSeek 适配器（V1.0 默认 Provider）。

接口文档：https://api-docs.deepseek.com/  （OpenAI 兼容协议）
说明：默认 base_url 为 https://api.deepseek.com，请求路径 /chat/completions。
如需切换模型，只需改环境变量 LLM_MODEL（如 deepseek-reasoner）。
"""
from __future__ import annotations

from app.core.config import Settings
from app.llm.openai_compatible import OpenAICompatibleProvider

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"


class DeepSeekProvider(OpenAICompatibleProvider):
    """DeepSeek 官方 API 适配。"""

    name = "deepseek"
    supports_json_mode = True

    def __init__(self, settings: Settings | None = None, *, model: str | None = None) -> None:
        super().__init__(settings, base_url=None, model=model)
        if not self._base_url or self._base_url == "https://api.openai.com":
            self._base_url = DEFAULT_BASE_URL
        if not self._model:
            self._model = DEFAULT_MODEL