"""测试用例生成与查询。"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DesignEngineDep, PipelineServiceDep, RepositoryDep
from app.schemas.api import ApiResponse, GenerateRequest, MethodInfo, ok
from app.schemas.testcase import TestCaseSuite

router = APIRouter(tags=["测试用例"])


@router.get("/testcases/methods", response_model=ApiResponse[list[MethodInfo]], summary="可用设计方法清单")
async def list_methods(engine: DesignEngineDep) -> dict:
    return ok([MethodInfo(**item) for item in engine.available_methods()])


@router.get("/testcases/suites", response_model=ApiResponse[list[TestCaseSuite]], summary="最近生成的用例集")
async def list_suites(repository: RepositoryDep, limit: int = Query(default=10, ge=1, le=50)) -> dict:
    return ok(repository.suites.list_recent(limit))


@router.post("/testcases/generate", response_model=ApiResponse[TestCaseSuite], summary="生成测试用例")
async def generate_testcases(payload: GenerateRequest, pipeline: PipelineServiceDep) -> dict:
    result = await pipeline.run(
        doc_id=payload.doc_id,
        text=payload.text,
        title=payload.title,
        methods=payload.methods,
        use_llm=payload.use_llm,
        use_llm_in_design=payload.use_llm_in_design,
        max_items=payload.max_items,
    )
    return ok(result.suite, message=f"已生成 {result.suite.stats.total} 条测试用例")


@router.get("/testcases/{suite_id}", response_model=ApiResponse[TestCaseSuite], summary="用例集详情")
async def get_suite(suite_id: str, repository: RepositoryDep) -> dict:
    return ok(repository.suites.get(suite_id))