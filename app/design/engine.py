"""设计引擎：把「结构化需求」按所选设计方法批量转换为「测试用例集」。

职责边界：
  - 只负责调度策略、隔离单个策略/单条需求的异常；
  - 不关心 LLM 细节（由 DesignContext 注入的 Provider 承担）；
  - 不关心导出格式（由 exporter 层承担）。
"""
from __future__ import annotations

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError, FeatureNotAvailableError, NotFoundError
from app.core.logging import get_logger
from app.core.utils import Timer, new_id
from app.design.base import DesignContext, DesignStrategy
from app.design.optimizer import optimize
from app.design.registry import STRATEGY_REGISTRY, available_methods, build_strategies
from app.llm.base import LLMProvider
from app.schemas.common import DesignMethod
from app.schemas.requirement import RequirementDoc, RequirementItem
from app.schemas.testcase import GenerationMeta, TestCase, TestCaseSuite

logger = get_logger(__name__)


class DesignEngine:
    """测试用例设计引擎。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    # ------------------------------------------------------------------ #
    def available_methods(self) -> list[dict]:
        return available_methods()

    def resolve_methods(self, methods: list[str | DesignMethod] | None) -> list[DesignMethod]:
        """把用户输入的方法名解析为枚举，并校验是否已实现。"""
        requested = methods or [DesignMethod.EQUIVALENCE, DesignMethod.BOUNDARY, DesignMethod.SCENARIO]
        resolved: list[DesignMethod] = []
        for raw in requested:
            try:
                method = raw if isinstance(raw, DesignMethod) else DesignMethod(str(raw).strip().lower())
            except ValueError as exc:
                raise NotFoundError(
                    f"未知的设计方法：{raw}，可选值：{', '.join(STRATEGY_REGISTRY.names())}",
                    detail={"available": STRATEGY_REGISTRY.names()},
                ) from exc
            if method not in resolved:
                resolved.append(method)

        unimplemented = [m.label for m in resolved if not STRATEGY_REGISTRY.get(m.value).implemented]
        if unimplemented:
            raise FeatureNotAvailableError(
                "以下设计方法已在架构中预留但尚未实现：" + "、".join(unimplemented),
                detail={
                    "unimplemented": unimplemented,
                    "implemented": [m.label for m in DesignMethod if STRATEGY_REGISTRY.try_get(m.value) and STRATEGY_REGISTRY.get(m.value).implemented],
                },
            )
        if not resolved:
            raise NotFoundError("至少需要选择一种设计方法。")
        return resolved

    # ------------------------------------------------------------------ #
    async def generate(
        self,
        doc: RequirementDoc,
        methods: list[str | DesignMethod] | None = None,
        *,
        llm: LLMProvider,
        use_llm: bool = False,
    ) -> TestCaseSuite:
        """对整份需求文档生成用例集。"""
        resolved = self.resolve_methods(methods)
        context = DesignContext(
            settings=self.settings,
            llm=llm,
            use_llm=use_llm,
            max_cases_per_item=self.settings.max_cases_per_requirement,
        )
        strategies = build_strategies(context)
        selected: list[DesignStrategy] = [strategies[method.value] for method in resolved]

        if use_llm and not llm.available:
            context.warn(f"未启用大模型（{llm.degraded_reason or '未配置'}），本次仅使用规则引擎生成用例。")

        cases: list[TestCase] = []
        with Timer() as timer:
            for item in doc.items:
                cases.extend(await self._generate_for_item(item, selected, context))

        unique_cases, duplicates = optimize(cases)

        suite = TestCaseSuite(
            suite_id=new_id("SUITE-"),
            doc_id=doc.doc_id,
            doc_title=doc.title,
            methods=resolved,
            cases=unique_cases,
            generation_meta=GenerationMeta(
                methods=[method.value for method in resolved],
                llm_used=context.llm_call_count > 0,
                llm_provider=llm.name,
                llm_model=llm.model,
                fallback_used=not llm.available,
                warnings=context.warnings,
                elapsed_ms=timer.elapsed_ms,
            ),
        )
        suite.stats.duplicate_removed = duplicates
        suite.recount()
        logger.info(
            "用例生成完成：doc=%s 方法=%s 用例数=%d（去重 %d）耗时=%dms",
            doc.doc_id,
            [m.value for m in resolved],
            suite.stats.total,
            duplicates,
            timer.elapsed_ms,
        )
        return suite

    # ------------------------------------------------------------------ #
    async def _generate_for_item(
        self,
        item: RequirementItem,
        strategies: list[DesignStrategy],
        context: DesignContext,
    ) -> list[TestCase]:
        cases: list[TestCase] = []
        for strategy in strategies:
            try:
                if not strategy.is_applicable(item):
                    continue
                produced = await strategy.generate(item)
            except AppError as exc:
                # 单条需求/单个方法的失败不应中断整体生成（关键异常路径兜底）
                context.warn(
                    f"需求「{item.title}」使用「{strategy.method.label}」生成失败（{exc.code}）：{exc.message}"
                )
                logger.warning("策略 %s 处理需求 %s 失败：%s", strategy.name, item.id, exc)
                continue
            except Exception as exc:  # noqa: BLE001 - 兜底：防止第三方异常导致整批失败
                context.warn(f"需求「{item.title}」使用「{strategy.method.label}」出现未知异常：{exc}")
                logger.exception("策略 %s 处理需求 %s 出现未知异常", strategy.name, item.id)
                continue
            cases.extend(produced)
        return cases