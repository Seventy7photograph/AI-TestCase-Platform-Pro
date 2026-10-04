"""健康检查与能力清单。"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DesignEngineDep, LLMDep, SettingsDep
from app.exporters.registry import available_formats
from app.integrations.base import available_integrations
from app.llm.factory import get_runtime_config_store
from app.parsers.registry import supported_extensions
from app.schemas.api import ApiResponse, HealthInfo, IntegrationInfo, MethodInfo, ok

router = APIRouter(tags=["健康检查"])


@router.get("/health", response_model=ApiResponse[HealthInfo], summary="健康检查与能力清单")
async def health(settings: SettingsDep, llm: LLMDep, engine: DesignEngineDep) -> dict:
    info = HealthInfo(
        app_name=settings.app_name,
        version=settings.app_version,
        status="ok",
        llm_provider=llm.name,
        llm_model=llm.model,
        llm_base_url=settings.llm_base_url,
        llm_available=llm.available,
        llm_degraded_reason=llm.degraded_reason,
        llm_source="runtime" if get_runtime_config_store().read() else "env",
        methods=[MethodInfo(**item) for item in engine.available_methods()],
        export_formats=available_formats(),
        supported_extensions=supported_extensions(),
    )
    return ok(info)


@router.get("/integrations", response_model=ApiResponse[list[IntegrationInfo]], summary="V3.0 外部集成清单")
async def integrations() -> dict:
    return ok(available_integrations())
