"""导出接口：Excel / JSON。"""
from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Response

from app.api.deps import ExportServiceDep
from app.exporters.registry import available_formats
from app.schemas.api import ApiResponse, ExportFormatInfo, ExportRequest, ok

router = APIRouter(tags=["导出"])


def build_download_response(content: bytes, filename: str, media_type: str) -> Response:
    """构造带中文文件名的下载响应（RFC 5987 filename*）。"""
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
            "X-Export-Filename": quote(filename),
        },
    )


@router.get("/export/formats", response_model=ApiResponse[list[ExportFormatInfo]], summary="可用导出格式")
async def list_formats() -> dict:
    return ok([ExportFormatInfo(**item) for item in available_formats()])


@router.post("/export", summary="导出用例集（返回文件流）")
async def export_suite(payload: ExportRequest, service: ExportServiceDep) -> Response:
    result = service.export_suite(payload.suite_id, payload.format)
    return build_download_response(result.content, result.filename, result.media_type)


@router.get("/export/{suite_id}/{fmt}", summary="按路径导出用例集（便于浏览器直接下载）")
async def export_suite_by_path(suite_id: str, fmt: str, service: ExportServiceDep) -> Response:
    result = service.export_suite(suite_id, fmt)
    return build_download_response(result.content, result.filename, result.media_type)