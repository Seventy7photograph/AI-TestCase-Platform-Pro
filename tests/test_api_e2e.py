"""端到端接口测试：上传 -> 解析 -> 生成 -> 导出，以及关键异常路径。

使用 sessions 级 TestClient（会触发 lifespan），LLM 走 FakeProvider，
因此整条链路在无网络、无 API Key 的情况下也能确定性验证。
"""
from __future__ import annotations

from urllib.parse import unquote

API = "/api/v1"

REQUIREMENT_MD = """# 用户注册需求

## 1、用户注册
手机号：11位数字，必填
年龄：18~120

主流程：
1. 进入注册页
2. 填写手机号
3. 提交注册

异常场景：
- 短信通道异常
"""


def _upload(client, content: str = REQUIREMENT_MD, filename: str = "需求.md"):
    return client.post(
        f"{API}/documents/upload",
        files={"file": (filename, content.encode("utf-8"), "text/markdown")},
    )


def test_health_reports_capabilities(client) -> None:
    response = client.get(f"{API}/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["llm_provider"] == "fake"
    assert data["llm_available"] is True
    methods = {item["name"]: item["implemented"] for item in data["methods"]}
    assert methods["equivalence"] and methods["boundary"] and methods["scenario"]
    assert methods["decision_table"] is False
    assert "excel" in {item["name"] for item in data["export_formats"]}
    assert "docx" in data["supported_extensions"]


def test_integrations_are_planned_not_implemented(client) -> None:
    body = client.get(f"{API}/integrations").json()
    mapping = {item["name"]: item["implemented"] for item in body["data"]}
    assert mapping == {"zentao": False, "jira": False}


def test_full_pipeline_via_upload(client) -> None:
    upload = _upload(client)
    assert upload.status_code == 200
    doc = upload.json()["data"]
    assert doc["char_count"] > 0
    doc_id = doc["doc_id"]

    parsed = client.post(
        f"{API}/requirements/parse", json={"doc_id": doc_id, "use_llm": True, "max_items": 5}
    )
    assert parsed.status_code == 200
    requirement = parsed.json()["data"]
    assert requirement["doc_id"] == doc_id
    assert requirement["items"]

    generated = client.post(
        f"{API}/testcases/generate",
        json={
            "doc_id": doc_id,
            "methods": ["equivalence", "boundary", "scenario"],
            "use_llm": True,
            "max_items": 5,
        },
    )
    assert generated.status_code == 200
    suite = generated.json()["data"]
    assert suite["stats"]["total"] > 0
    assert suite["doc_id"] == doc_id

    detail = client.get(f"{API}/testcases/{suite['suite_id']}")
    assert detail.json()["data"]["stats"]["total"] == suite["stats"]["total"]


def test_pipeline_endpoint_returns_requirement_and_suite(client) -> None:
    response = client.post(
        f"{API}/pipeline/generate",
        json={
            "text": REQUIREMENT_MD,
            "title": "注册需求",
            "methods": ["equivalence", "boundary", "scenario"],
            "use_llm": True,
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["requirement_doc"]["items"]
    assert data["suite"]["cases"]
    assert isinstance(data["warnings"], list)
    assert data["suite"]["generation_meta"]["methods"] == ["equivalence", "boundary", "scenario"]


def test_export_excel_and_json(client) -> None:
    suite = client.post(
        f"{API}/pipeline/generate",
        json={"text": REQUIREMENT_MD, "title": "导出用例", "methods": ["boundary"], "use_llm": False},
    ).json()["data"]["suite"]

    excel = client.post(f"{API}/export", json={"suite_id": suite["suite_id"], "format": "excel"})
    assert excel.status_code == 200
    assert excel.content[:2] == b"PK"
    disposition = excel.headers["content-disposition"]
    assert "filename*=UTF-8''" in disposition
    assert "测试用例" in unquote(disposition)

    download = client.get(f"{API}/export/{suite['suite_id']}/json")
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("application/json")

    formats = client.get(f"{API}/export/formats").json()["data"]
    assert {item["name"] for item in formats} == {"excel", "json"}


def test_export_unknown_suite_returns_404(client) -> None:
    response = client.post(f"{API}/export", json={"suite_id": "SUITE-nope", "format": "excel"})
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False and body["code"] == "NOT_FOUND"


def test_export_unknown_format_returns_404(client) -> None:
    suite = client.post(
        f"{API}/pipeline/generate", json={"text": REQUIREMENT_MD, "methods": ["boundary"], "use_llm": False}
    ).json()["data"]["suite"]
    response = client.post(f"{API}/export", json={"suite_id": suite["suite_id"], "format": "xmind"})
    assert response.status_code == 404


def test_upload_unsupported_format_returns_415(client) -> None:
    response = client.post(
        f"{API}/documents/upload",
        files={"file": ("需求.xlsx", b"binary", "application/vnd.ms-excel")},
    )
    assert response.status_code == 415
    assert response.json()["code"] == "UNSUPPORTED_FORMAT"


def test_upload_empty_file_returns_422(client) -> None:
    response = client.post(f"{API}/documents/upload", files={"file": ("empty.txt", b"", "text/plain")})
    assert response.status_code == 422
    assert response.json()["code"] == "DOCUMENT_PARSE_FAILED"


def test_v2_design_method_returns_501(client) -> None:
    response = client.post(
        f"{API}/testcases/generate",
        json={"text": REQUIREMENT_MD, "methods": ["decision_table"], "use_llm": False},
    )
    assert response.status_code == 501
    body = response.json()
    assert body["code"] == "FEATURE_NOT_AVAILABLE"
    assert body["detail"]["unimplemented"] == ["判定表"]


def test_unknown_method_returns_404(client) -> None:
    response = client.post(
        f"{API}/testcases/generate", json={"text": REQUIREMENT_MD, "methods": ["nope"], "use_llm": False}
    )
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_missing_source_returns_400(client) -> None:
    response = client.post(f"{API}/testcases/generate", json={"methods": ["boundary"]})
    assert response.status_code == 400
    assert response.json()["code"] == "BAD_REQUEST"


def test_validation_error_returns_422_envelope(client) -> None:
    response = client.post(f"{API}/requirements/parse", json={"max_items": 999})
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["success"] is False


def test_requirement_not_found(client) -> None:
    response = client.get(f"{API}/requirements/DOC-missing")
    assert response.status_code == 404


def test_documents_listing(client) -> None:
    _upload(client, "# 列表需求\n## 功能A\n描述A\n", "list.md")
    body = client.get(f"{API}/documents", params={"limit": 5}).json()
    assert body["success"] is True
    assert len(body["data"]) >= 1


def test_index_page_served(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "AI 测试用例生成助手" in response.text


def test_pipeline_exposes_both_llm_stages(client) -> None:
    """展示口径回归：解析阶段与生成阶段必须分别可观测，不能混为一谈。"""
    data = client.post(
        f"{API}/pipeline/generate",
        json={
            "text": REQUIREMENT_MD,
            "title": "两阶段口径",
            "methods": ["equivalence", "boundary", "scenario"],
            "use_llm": True,
            "use_llm_in_design": True,
        },
    ).json()["data"]

    assert data["requirement_doc"]["parse_meta"]["llm_used"] is True
    assert data["suite"]["generation_meta"]["llm_used"] is True
    # 解析口径快照应随用例集一同落盘，供导出/展示复用
    assert data["suite"]["parse_meta"]["llm_used"] is True
    assert data["suite"]["parse_meta"]["provider"] == "fake"


def test_pipeline_rule_only_design_reports_rule_engine(client) -> None:
    """未开启生成阶段 LLM 时，生成口径必须如实显示为规则引擎。"""
    data = client.post(
        f"{API}/pipeline/generate",
        json={
            "text": REQUIREMENT_MD,
            "title": "纯规则生成",
            "methods": ["equivalence"],
            "use_llm": True,
            "use_llm_in_design": False,
        },
    ).json()["data"]

    assert data["suite"]["generation_meta"]["llm_used"] is False
    assert data["requirement_doc"]["parse_meta"]["llm_used"] is True


def test_persisted_suite_keeps_parse_snapshot(client) -> None:
    """用例集详情接口也应返回解析口径快照（前端展示依赖它）。"""
    suite = client.post(
        f"{API}/pipeline/generate",
        json={"text": REQUIREMENT_MD, "title": "口径快照", "methods": ["boundary"], "use_llm": True},
    ).json()["data"]["suite"]
    detail = client.get(f"{API}/testcases/{suite['suite_id']}").json()["data"]
    assert detail["parse_meta"]["llm_used"] is True
