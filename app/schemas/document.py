"""已上传文档的记录模型（元信息 + 抽取文本）。"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.utils import now_iso


class DocumentRecord(BaseModel):
    doc_id: str
    filename: str
    extension: str
    size_bytes: int
    text: str = ""
    char_count: int = 0
    line_count: int = 0
    encoding: str = "utf-8"
    stored_path: str = ""
    parser: str = ""
    page_count: int | None = None
    table_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)

    def preview(self, limit: int = 500) -> str:
        from app.core.utils import truncate

        return truncate(self.text, limit)


class DocumentSummary(BaseModel):
    """上传接口返回体（不回传全文，避免响应体过大）。"""

    doc_id: str
    filename: str
    extension: str
    size_bytes: int
    char_count: int
    line_count: int
    encoding: str = "utf-8"
    parser: str
    page_count: int | None = None
    table_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    created_at: str = ""
    preview: str = ""

    @classmethod
    def from_record(cls, record: DocumentRecord) -> "DocumentSummary":
        return cls(
            doc_id=record.doc_id,
            filename=record.filename,
            extension=record.extension,
            size_bytes=record.size_bytes,
            char_count=record.char_count,
            line_count=record.line_count,
            encoding=record.encoding,
            parser=record.parser,
            page_count=record.page_count,
            table_count=record.table_count,
            warnings=record.warnings,
            created_at=record.created_at,
            preview=record.preview(),
        )
