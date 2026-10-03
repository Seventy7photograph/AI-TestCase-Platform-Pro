"""文档上传与查询。"""
from __future__ import annotations

from fastapi import APIRouter, File, Query, UploadFile

from app.api.deps import DocumentServiceDep
from app.schemas.api import ApiResponse, ok
from app.schemas.document import DocumentSummary

router = APIRouter(tags=["文档"])


@router.post(
    "/documents/upload",
    response_model=ApiResponse[DocumentSummary],
    summary="上传并解析需求文档（docx/pdf/txt/md/csv/json）",
)
async def upload_document(service: DocumentServiceDep, file: UploadFile = File(...)) -> dict:
    data = await file.read()
    record = service.save_and_parse(filename=file.filename or "", data=data)
    return ok(DocumentSummary.from_record(record), message="文档解析成功")


@router.get("/documents", response_model=ApiResponse[list[DocumentSummary]], summary="最近上传的文档")
async def list_documents(service: DocumentServiceDep, limit: int = Query(default=20, ge=1, le=100)) -> dict:
    records = service.list_recent(limit)
    return ok([DocumentSummary.from_record(record) for record in records])


@router.get("/documents/{doc_id}", response_model=ApiResponse[DocumentSummary], summary="文档详情")
async def get_document(doc_id: str, service: DocumentServiceDep) -> dict:
    return ok(DocumentSummary.from_record(service.get(doc_id)))