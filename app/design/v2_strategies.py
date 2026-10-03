"""V2.0 设计策略预留位（仅定义接口，不实现逻辑）。

显式占位而非留空的意义：
  1. 让「能力清单」接口能对外暴露路线图；
  2. 调用时返回 501 + 明确版本说明，前端可以直接提示"即将支持"；
  3. 后续实现时只需替换 generate() 内部，无需改动注册与调用链。
"""
from __future__ import annotations

from app.design.base import DesignStrategy, NotImplementedStrategy
from app.schemas.common import DesignMethod


class DecisionTableStrategy(NotImplementedStrategy):
    """V2.0：判定表法（多条件组合 -> 动作）。"""

    method = DesignMethod.DECISION_TABLE
    description = "V2.0 规划：按条件桩/动作桩生成判定表并压缩等价规则，适合多条件组合业务校验。"


class CauseEffectStrategy(NotImplementedStrategy):
    """V2.0：因果图法。"""

    method = DesignMethod.CAUSE_EFFECT
    description = "V2.0 规划：基于原因-结果图识别约束关系（异或/包含/屏蔽），生成判定表再转用例。"


class OrthogonalStrategy(NotImplementedStrategy):
    """V2.0：正交实验法。"""

    method = DesignMethod.ORTHOGONAL
    description = "V2.0 规划：为多因子多水平场景构造正交表，用最少用例覆盖两两组合。"


__all__ = [
    "DecisionTableStrategy",
    "CauseEffectStrategy",
    "OrthogonalStrategy",
    "DesignStrategy",
]