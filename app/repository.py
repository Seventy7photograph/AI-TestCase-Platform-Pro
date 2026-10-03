"""极简持久化层（V1.0 采用 JSON 文件存储，零外部依赖、开箱即跑）。

为什么不是 SQLAlchemy：
  V1.0 的目标是"单机可跑通"，引入数据库会增加部署成本；
  但持久化被收敛在 JsonObjectStore 内部，V2.0 只需新增 SqlObjectStore
  并替换 build_repository() 的装配，业务层（services/api）无需改动。
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError, NotFoundError
from app.core.logging import get_logger
from app.schemas.document import DocumentRecord
from app.schemas.requirement import RequirementDoc
from app.schemas.testcase import TestCaseSuite

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

SAFE_ID_RE = re.compile(r"[^0-9A-Za-z_\-]")


class StorageCorruptedError(AppError):
    code = "STORAGE_CORRUPTED"
    http_status = 500
    default_message = "本地存储数据损坏，无法读取"


def safe_id(raw: object) -> str:
    """把外部传入的 ID 规整为安全文件名，杜绝路径穿越。"""
    cleaned = SAFE_ID_RE.sub("", str(raw or ""))
    if not cleaned:
        raise NotFoundError("非法的资源 ID。", detail={"raw": str(raw)})
    return cleaned


class JsonObjectStore(Generic[T]):
    """把 Pydantic 模型以 JSON 文件形式落盘（一对象一文件）。"""

    def __init__(self, directory: Path, model: type[T], *, id_attr: str, label: str) -> None:
        self.directory = Path(directory)
        self.model = model
        self.id_attr = id_attr
        self.label = label
        self.directory.mkdir(parents=True, exist_ok=True)

    def path_for(self, obj_id: object) -> Path:
        return self.directory / f"{safe_id(obj_id)}.json"

    def save(self, obj: T) -> T:
        obj_id = getattr(obj, self.id_attr)
        path = self.path_for(obj_id)
        tmp_path = path.with_suffix(".json.tmp")
        tmp_path.write_text(obj.model_dump_json(indent=2), encoding="utf-8")
        os.replace(tmp_path, path)
        logger.debug("保存 %s：%s", self.label, path.name)
        return obj

    def exists(self, obj_id: object) -> bool:
        try:
            return self.path_for(obj_id).exists()
        except NotFoundError:
            return False

    def get(self, obj_id: object) -> T:
        path = self.path_for(obj_id)
        if not path.exists():
            raise NotFoundError(
                f"{self.label}不存在：{obj_id}",
                detail={"kind": self.label, "id": str(obj_id)},
            )
        try:
            return self.model.model_validate_json(path.read_text(encoding="utf-8"))
        except ValidationError as exc:
            raise StorageCorruptedError(
                f"{self.label}（{obj_id}）内容损坏，无法反序列化。",
                detail={"path": str(path), "error": exc.error_count()},
            ) from exc
        except OSError as exc:
            raise StorageCorruptedError(
                f"{self.label}（{obj_id}）读取失败：{exc}", detail={"path": str(path)}
            ) from exc

    def try_get(self, obj_id: object) -> T | None:
        try:
            return self.get(obj_id)
        except (NotFoundError, StorageCorruptedError):
            return None

    def delete(self, obj_id: object) -> bool:
        path = self.path_for(obj_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_recent(self, limit: int = 20) -> list[T]:
        files = sorted(self.directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        results: list[T] = []
        for path in files[: max(limit, 0)]:
            try:
                results.append(self.model.model_validate_json(path.read_text(encoding="utf-8")))
            except (ValidationError, OSError):
                logger.warning("跳过损坏的存储文件：%s", path.name)
        return results

    def count(self) -> int:
        return len(list(self.directory.glob("*.json")))


class Repository:
    """业务侧统一门面（依赖倒置：业务只依赖它，不依赖具体存储实现）。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        base = self.settings.data_dir
        self.documents: JsonObjectStore[DocumentRecord] = JsonObjectStore(
            base / "documents", DocumentRecord, id_attr="doc_id", label="文档"
        )
        self.requirements: JsonObjectStore[RequirementDoc] = JsonObjectStore(
            base / "requirements", RequirementDoc, id_attr="doc_id", label="需求解析结果"
        )
        self.suites: JsonObjectStore[TestCaseSuite] = JsonObjectStore(
            base / "suites", TestCaseSuite, id_attr="suite_id", label="用例集"
        )


@lru_cache(maxsize=1)
def get_repository() -> Repository:
    return Repository(get_settings())


def reset_repository_cache() -> None:
    get_repository.cache_clear()