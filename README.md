# AI 测试用例生成助手 v1.1.0

[![CI](https://github.com/Seventy7photograph/AI-TestCase-Platform-Pro/actions/workflows/ci.yml/badge.svg)](https://github.com/Seventy7photograph/AI-TestCase-Platform-Pro/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3-42b883.svg)](https://vuejs.org/)
[![Version](https://img.shields.io/badge/version-v1.1.0-blue.svg)](CHANGELOG.md)

> 基于 **Python + FastAPI** 的测试用例生成服务：把需求文档一键转换为结构化需求模型，
> 再经 **等价类划分 / 边界值分析 / 场景法** 三类设计方法生成测试用例，最后导出 Excel。
> 调用 DeepSeek 等大模型辅助理解需求，**未配置 API Key 时自动降级为纯规则引擎，链路依然端到端可用**。

**导航**：[快速开始](#三快速开始) · [接口清单](#五接口清单) · [架构与扩展点](#六架构与扩展点) ·
[常见问题](#十一常见问题faq) · [路线图](ROADMAP.md) · [更新日志](CHANGELOG.md) ·
[贡献指南](CONTRIBUTING.md) · [安全策略](SECURITY.md)

---

## 一、能力范围

**已实现（端到端可跑通）**

| 能力 | 说明 |
| --- | --- |
| 文档上传与解析 | `.docx` / `.pdf` / `.txt` / `.md` / `.csv` / `.json`，兼容 GBK 等中文编码，Word 表格结构化平铺 |
| 需求结构化解析 | LLM 结构化抽取 + 规则引擎解析双路，LLM 缺失/失败自动降级并显式告警 |
| 测试设计引擎 | 等价类划分、边界值分析（min-1/min/min+1/max-1/max/max+1）、场景法（主流程/备选流/异常流/业务规则） |
| 用例优化 | 两层去重（精确指纹 + 跨方法语义重叠，合并关联需求并记录覆盖方法）、优先级排序、按方法自动编号（TC-EQ/BV/SC） |
| Excel 导出 | 4 个 Sheet：用例明细 / 用例统计 / 需求追溯 / 生成信息；另提供 JSON 导出 |
| 统一异常出口 | 所有错误返回 `{success, code, message, detail}` |

**架构预留（V2.0 / V3.0，只定义接口，不实现逻辑）**

- 设计策略：判定表、因果图、正交实验（调用返回 501 + 版本说明）
- 导出器：XMind / CSV / TestLink XML（注册表已就绪）
- LLM Provider：Qwen / GLM / 本地 Ollama（注册表已就绪）
- 外部集成：禅道 / Jira（`ExternalSyncAdapter` 抽象已定义）

---

## 二、目录结构

```
AI-TestCase-Platform-Pro-v1.0/
├── app/
│   ├── main.py                     # FastAPI 装配入口（中间件/异常处理/路由/静态页）
│   ├── repository.py               # 持久化门面 + JSON 文件存储实现
│   ├── core/
│   │   ├── config.py               # 配置（环境变量 > .env > 默认值）
│   │   ├── exceptions.py           # 统一异常体系（含 HTTP 状态码与错误码）
│   │   ├── logging.py              # 日志初始化
│   │   ├── registry.py             # 通用插件注册表（策略/导出器/Provider 共用）
│   │   └── utils.py                # ID/编码/JSON 容错解析/计时
│   ├── schemas/
│   │   ├── common.py               # 领域枚举（设计方法/优先级/用例类型/字段类型）
│   │   ├── requirement.py          # 结构化需求模型（整条流水线的中间表示）
│   │   ├── testcase.py             # 测试用例与用例集统计模型
│   │   ├── document.py             # 文档记录模型
│   │   └── api.py                  # HTTP 请求/响应契约
│   ├── llm/                        # ① LLM Provider 抽象层
│   │   ├── base.py                 # LLMProvider 抽象 + JSON 重试修复
│   │   ├── openai_compatible.py    # OpenAI 兼容协议实现
│   │   ├── deepseek_provider.py    # DeepSeek 适配（V1.0 默认）
│   │   ├── null_provider.py        # 未配置密钥时的降级实现
│   │   ├── fake_provider.py        # 离线确定性实现（测试/演示）
│   │   ├── factory.py              # Provider 工厂 + 注册表
│   │   └── prompts.py              # Prompt 模板集中管理
│   ├── parsers/                    # 文档解析层
│   │   ├── base.py                 # DocumentParser 抽象
│   │   ├── text_parser.py          # txt/md/csv/json（多编码兼容）
│   │   ├── docx_parser.py          # Word（标题层级 + 表格还原）
│   │   ├── pdf_parser.py           # PDF（pypdf）
│   │   └── registry.py             # 解析器注册表与分发
│   ├── design/                     # ② 设计策略抽象层
│   │   ├── base.py                 # DesignStrategy 抽象 + DesignContext + 占位策略
│   │   ├── equivalence.py          # 等价类划分
│   │   ├── boundary.py             # 边界值分析
│   │   ├── scenario.py             # 场景法（可叠加 LLM 增强）
│   │   ├── v2_strategies.py        # V2.0 策略占位
│   │   ├── optimizer.py            # 用例去重/排序/编号
│   │   ├── engine.py               # 设计引擎调度
│   │   └── registry.py             # 设计策略注册表
│   ├── exporters/                  # ③ 导出器抽象层
│   │   ├── base.py                 # Exporter 抽象 + ExportResult
│   │   ├── excel_exporter.py       # Excel 导出（openpyxl）
│   │   ├── json_exporter.py        # JSON 导出
│   │   └── registry.py             # 导出器注册表
│   ├── integrations/base.py        # ④ 外部集成抽象（V3.0 预留）
│   ├── services/
│   │   ├── document_service.py     # 上传校验 + 解析 + 落盘
│   │   ├── rule_parser.py          # 规则化需求解析器（确定性兜底链路）
│   │   ├── requirement_service.py  # 需求结构化解析（LLM + 规则双路）
│   │   ├── export_service.py       # 导出编排 + 归档
│   │   └── pipeline_service.py     # 一键流水线编排
│   ├── api/
│   │   ├── deps.py                 # 依赖注入装配点
│   │   └── routes/                 # health / documents / requirements / testcases / export / pipeline
│   └── static/                     # 前端构建产物（Vue 3 SPA，由 frontend/ 构建输出）
├── frontend/                       # 前端工程（Vue 3 + TypeScript + Vite + Element Plus）
│   ├── src/                        # 视图、组件、设计令牌、API 客户端
│   │   ├── styles/tokens.css       # 设计令牌（冷调纸白 / 冰川蓝 / 密度档位）
│   │   ├── components/             # AppShell / CabinetRail / TraceCard / CaseTable ...
│   │   └── views/                  # 工作台 / 文档与需求 / 用例集 / 运行状态
│   ├── legacy/index.html           # 重构前的单文件演示页（仅作留档）
│   ├── tools/                      # 本地截图与量测脚本（开发用）
│   └── package.json
├── DESIGN.md                       # 视觉设计系统（令牌 + 应用规则）
├── PRODUCT.md                      # 产品上下文（用户 / 定位 / 约束）
├── tests/                          # 100 项 pytest 测试
├── examples/
│   ├── sample_requirement.md       # 示例需求文档
│   ├── demo_offline.py             # 离线端到端演示脚本
│   ├── acceptance_check.py         # 黑盒验收脚本（启动真实服务走 HTTP 验证全链路）
│   └── api_examples.md             # 接口调用示例（curl / PowerShell / Python）
├── requirements.txt / requirements-dev.txt
├── .env.example / .gitignore
├── pytest.ini
└── run.py                          # 本地启动入口
```

---

## 三、快速开始

### 1. 环境要求

- Python **3.10+**（实测 3.11）
- 无需数据库、无需 Docker，默认使用 JSON 文件存储

### 2. 安装

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

> **Windows 常见问题**：若 `pip install` 报 `UnicodeDecodeError: 'gbk' codec can't decode byte ...`
> （旧版 pip 按系统本地编码读取 UTF-8 依赖文件所致），先执行 `python -m pip install -U pip` 升级 pip 即可。
> 建议使用 **PowerShell 7（`pwsh`）** 而非 Windows PowerShell 5.1。

### 3. 配置

```bash
# Windows PowerShell
Copy-Item .env.example .env
# macOS / Linux
# cp .env.example .env
```

`.env` 关键项：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `LLM_PROVIDER` | `deepseek` | `deepseek` / `openai_compatible` / `fake` / `none`（纯规则引擎） |
| `LLM_API_KEY` | 空 | **必须通过环境变量注入，禁止硬编码**；为空时自动降级规则引擎 |
| `LLM_BASE_URL` | `https://api.deepseek.com` | OpenAI 兼容端点 |
| `LLM_MODEL` | `deepseek-chat` | 也可填 `deepseek-reasoner` |
| `STORAGE_DIR` | `./storage` | 上传文件、解析结果、用例集、导出归档 |
| `MAX_UPLOAD_SIZE_MB` | `20` | 上传大小上限 |
| `MAX_CASES_PER_REQUIREMENT` | `60` | 单条需求用例数上限（防边界值爆炸） |

> **不配置 `LLM_API_KEY` 也能完整跑通**：系统会记录降级原因，并在响应告警与 Excel「生成信息」页中可见。
>
> `.env` 是**基线配置**（启动即用、无人值守也能跑）；前端「运行状态 → 大模型配置」可在此基础上做**运行时覆盖**，两者不冲突，详见下文。

### 4. 启动

```bash
python run.py
# 或
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- 前端界面（SPA）：http://127.0.0.1:8000/
- 接口文档：http://127.0.0.1:8000/docs
- 前端路由由后端 SPA 回退承接：非 `api/`、`openapi.json`、`docs` 前缀的路径一律返回 `app/static/index.html`

> **务必用 `127.0.0.1` 或 `localhost` 访问，不要用 `http://0.0.0.0:8000/`。**
> `0.0.0.0` 是"监听全部网卡"的绑定地址，不是可访问的目的地址；开启系统代理时
> 浏览器会把它交给代理，代理无法解析该目标而返回 **502 Bad Gateway**。
> 启动脚本 `run.py` 已内置该提示与参数支持：
>
> ```bash
> python run.py --port 8080        # 换端口
> python run.py --host 127.0.0.1   # 只监听本机（更安全）
> python run.py --no-reload        # 关闭热重载
> ```

### 5. 前端开发与构建

界面是 **Vue 3 + TypeScript + Vite + Element Plus** 单页应用，源码在 `frontend/`，构建产物直接写入 `app/static/`（由 FastAPI 在 `/` 提供）。

```bash
cd frontend
npm install          # 首次安装依赖
npm run dev          # 开发服务器 http://127.0.0.1:5173，/api 代理到 127.0.0.1:8000
npm run build        # vue-tsc 类型检查 + vite 构建，输出到 ../app/static
```

> 修改 `frontend/src/**` 后必须重新执行 `npm run build`：`app/static/` 是构建产物，不是源码。
> 视觉令牌集中在 `frontend/src/styles/tokens.css`；设计系统说明见 `DESIGN.md`，产品上下文见 `PRODUCT.md`。

界面主题是**蓝白 + 冰川蓝**（冷调纸白纸面、深墨蓝导轨、冰川蓝作唯一强调色）。改色只需动令牌里的三档蓝再重新构建：

| 令牌 | 值 | 用途 |
| --- | --- | --- |
| `--stamp` | `#1a7fa9` | 面：主按钮底、选中底、焦点描边、覆盖率条 |
| `--stamp-deep` | `#12607f` | 字：链接、悬停文字、印章编号字 |
| `--stamp-wash` | `#e2f1f8` | 底：印章编号底、表格行悬停、选区 |

> 浅色底上的蓝色文字必须用 `--stamp-deep`：`--stamp` 在纸面 `#eef2f5` 上只有 4.01:1，不足 WCAG AA 的 4.5:1。
> 后端在 `app/main.py` 中显式注册了 `.js` / `.mjs` 的 MIME 类型，避免 Windows 把模块脚本识别成 `text/plain`。

### 6. 一分钟验证

```bash
# 离线端到端演示（无需任何 API Key，产出 output/*.xlsx）
python examples/demo_offline.py

# 黑盒验收：启动真实服务，走 HTTP 验证全链路与异常路径
python examples/acceptance_check.py

# 运行单元/接口测试
python -m pytest
```

---

## 四、核心链路

```
              ┌──────────────┐
  上传文档 →  │ parsers 解析层 │ → 纯文本（docx 表格结构化平铺）
              └──────────────┘
                     ↓
        ┌────────────────────────────┐
        │ requirement_service         │  ① LLM 结构化抽取（prompts.py）
        │ 需求 → RequirementDoc(IR)   │  ② 失败/未配置 → rule_parser 规则兜底
        └────────────────────────────┘     ③ 两路字段互补（difflib 相似度匹配）
                     ↓
        ┌────────────────────────────┐
        │ design/engine 设计引擎      │  EquivalenceStrategy
        │ 策略注册表 + 逐条需求调度     │  BoundaryStrategy
        └────────────────────────────┘  ScenarioStrategy（可选 LLM 增强）
                     ↓
        ┌────────────────────────────┐
        │ optimizer 用例优化          │  指纹去重 → 排序 → TC-XX-NNN 编号
        └────────────────────────────┘
                     ↓
        ┌────────────────────────────┐
        │ exporters 导出层            │  Excel（4 Sheet）/ JSON
        └────────────────────────────┘
```

**为什么把「需求解析」和「用例生成」拆成两次 LLM 调用？**
单次 Prompt 同时做"理解需求"和"设计用例"会导致输出不稳定、难以校验。
拆开后：第一段输出受 Pydantic 模型强约束（可校验、可兜底），
第二段只在"需要 LLM 补充易漏场景"时触发，成本与失败面都更小。

---

## 五、接口清单

统一响应结构：`{"success": bool, "code": str, "message": str, "data": any}`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/health` | 健康检查 + 能力清单（设计方法/导出格式/支持的扩展名/LLM 状态） |
| GET | `/api/v1/integrations` | V3.0 外部集成清单（禅道/Jira，均为未实现状态） |
| POST | `/api/v1/documents/upload` | 上传并解析需求文档（multipart/form-data） |
| GET | `/api/v1/documents` | 最近上传的文档 |
| GET | `/api/v1/documents/{doc_id}` | 文档详情（含文本预览） |
| POST | `/api/v1/requirements/parse` | 需求解析为结构化模型（`doc_id` 或 `text` 二选一） |
| GET | `/api/v1/requirements/{doc_id}` | 获取已解析的需求模型 |
| POST | `/api/v1/requirements/{doc_id}/testcases` | 基于已解析需求直接生成用例 |
| POST | `/api/v1/testcases/generate` | 生成测试用例（返回用例集） |
| GET | `/api/v1/testcases/methods` | 设计方法清单（含未实现的规划项） |
| GET | `/api/v1/testcases/suites` | 最近生成的用例集 |
| GET | `/api/v1/testcases/{suite_id}` | 用例集详情 |
| POST | `/api/v1/pipeline/generate` | **一键流水线**：需求 → 结构化需求 → 用例 |
| GET | `/api/v1/export/formats` | 可用导出格式 |
| POST | `/api/v1/export` | 导出用例集（返回文件流，`Content-Disposition` 支持中文名） |
| GET | `/api/v1/export/{suite_id}/{fmt}` | 浏览器直接下载（`fmt` = `excel` / `json`） |

完整调用示例见 [`examples/api_examples.md`](examples/api_examples.md)。

最小示例：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/pipeline/generate \
  -H "Content-Type: application/json" \
  -d '{
        "text": "## 用户注册\n手机号：11位数字，必填\n年龄：18~120",
        "title": "注册需求",
        "methods": ["equivalence", "boundary", "scenario"],
        "use_llm": true
      }'
```

---

## 六、架构与扩展点

三类抽象接口都已落地为**注册表 + 依赖注入**，追加能力不需要改主干代码。

### 1. 设计策略（`app/design/`）

```python
class DesignStrategy(ABC):
    method: DesignMethod
    def is_applicable(self, item: RequirementItem) -> bool: ...
    async def generate(self, item: RequirementItem) -> list[TestCase]: ...
```

新增「判定表」只需：

```python
# app/design/decision_table.py
class DecisionTableStrategy(DesignStrategy):
    method = DesignMethod.DECISION_TABLE
    async def generate(self, item): ...

# app/design/registry.py
register_strategy(DecisionTableStrategy)   # 一行接入，API/前端自动感知
```

### 2. 导出器（`app/exporters/`）

```python
class Exporter(ABC):
    name: str; label: str; extension: str; media_type: str
    def export(self, suite: TestCaseSuite, *, options: dict | None = None) -> ExportResult: ...
```

V2.0 增加 XMind：实现 `XmindExporter` 后 `register_exporter(XmindExporter())` 即可，
`/export/formats` 与前端下拉框自动出现新格式。

### 3. LLM Provider（`app/llm/`）

```python
class LLMProvider(ABC):
    name: str
    @property
    def available(self) -> bool: ...
    async def complete(self, messages, *, temperature=None, max_tokens=None, json_mode=False) -> LLMResponse: ...
    async def complete_json(self, messages, *, expect=(dict, list)) -> LLMResponse: ...
```

接入 Qwen：实现子类 + `PROVIDER_REGISTRY.register("qwen", ...)`，
再把 `.env` 的 `LLM_PROVIDER` 改成 `qwen` 即可 —— 业务层零改动。

**运行时切换（界面，无需重启）**：前端「运行状态 → 大模型配置」可切换厂商 / 模型 / 端点 / Key /
温度等，并提供「测试连接」与「拉取模型」；保存后写入 `storage/data/llm_config.json`（已 gitignore，
密钥不出本机、接口只回显掩码）。优先级为 `界面覆盖 > .env > 代码默认值`，
「恢复 .env 配置」可随时回到基线。

| 接口 | 说明 |
| --- | --- |
| `GET /api/v1/llm/config` | 读取生效配置（含掩码 Key）与候选厂商 / 模型目录 |
| `PUT /api/v1/llm/config` | 保存界面覆盖，立即对后续解析 / 生成生效 |
| `DELETE /api/v1/llm/config` | 清除界面覆盖，恢复 `.env` 基线 |
| `POST /api/v1/llm/config/test` | 用当前配置或未保存的表单值做一次真实连通性测试 |
| `GET /api/v1/llm/models` | 拉取候选模型（厂商 `/models`，失败回退内置目录） |

### 4. 外部集成（`app/integrations/`，V3.0）

```python
class ExternalSyncAdapter(ABC):
    async def push_cases(self, suite, *, project_key="", options=None) -> SyncResult: ...
    async def pull_requirements(self, *, project_key="", options=None) -> list[str]: ...
    async def health_check(self) -> bool: ...
```

### 5. 持久化

V1.0 使用 `JsonObjectStore`（一对象一 JSON 文件，原子写入，ID 白名单防路径穿越）。
V2.0 换数据库时，只需新增 `SqlObjectStore` 并替换 `build_repository()` 装配，业务层不变。

---

## 七、关键异常路径与兜底策略

| 异常路径 | 处理策略 | 用户可见结果 |
| --- | --- | --- |
| 文件过大（> `MAX_UPLOAD_SIZE_MB`） | 快速失败，不读取解析 | `413` `PAYLOAD_TOO_LARGE` |
| 不支持的扩展名 / 无扩展名 | 按注册表校验并给出支持列表 | `415` `UNSUPPORTED_FORMAT` |
| 文档损坏（docx/pdf 解析异常） | 统一包装，提示另存 txt/md | `422` `DOCUMENT_PARSE_FAILED` |
| 空文件 / 扫描件 PDF 抽不到文字 | 抽取长度阈值校验 + 提示不支持 OCR | `422` `DOCUMENT_EMPTY` |
| **LLM 未配置 API Key** | **自动降级规则引擎**，记录降级原因 | 正常返回 + 告警可见 |
| LLM 网络超时 / HTTP 错误 | 降级规则引擎，保留错误详情 | 正常返回 + 告警可见 |
| **LLM 返回非 JSON** | 剥离代码块/去注释/去尾逗号/中文引号修复，失败追加"修复指令"重试（默认 2 次） | 自动修复或降级 |
| LLM 返回字段缺失 | 宽松 Pydantic 模型（`extra=ignore` + 逐字段默认值与类型强制），缺失即降级 | 正常返回 |
| LLM 未解析出任何条目 | 降级规则解析 | 正常返回 + 告警可见 |
| 字段无法抽取风险 | 无字段时等价类降级为「正常/异常」两类并告警 | 用例仍可生成 |
| **规则也解析不出需求** | 整篇作为单条需求，并提示建议 LLM 解析 | 正常返回 + 告警可见 |
| 单个策略 / 单条需求失败 | 引擎捕获并跳过，不中断整批生成 | 其余用例正常产出 |
| **跨方法重复用例**（等价类与边界值对同一测试点各产一条） | 语义重叠去重合并为一条，`covered_methods` 记录全部覆盖方法 | 用例集不虚高 |
| **等长字段的越界点被误判为有效**（如 `min_length == max_length == 6` 时的 7 位） | 同一取值被两条约束分别判为有效/越界时，以「越界」为准 | 用例类型正确，不会出现"预期成功但实际被拒" |
| 用例数量爆炸 | `MAX_CASES_PER_REQUIREMENT` 截断 + 告警 | 正常返回 + 告警可见 |
| **Tab 分隔表格（Word/网页粘贴）** | 按「表头 + 列数一致」识别为表格；不满足则按正文处理 | 字段约束正常抽取 |
| **疑似表格却抽不出字段** | 检测到表头特征但 0 字段时给出可操作告警 | 正常返回 + 告警可见 |
| 「长度 2~20」等无单位长度范围 | 优先按长度约束解析，不再误判为数值区间 | 约束抽取正确 |
| 数字串字段（11位数字/验证码） | 数值填充（"1"），而非字母 "A" | 测试数据满足字段约束 |
| 手机号/身份证等内置格式字段 | 有效等价类使用符合正则的样例值 | 有效数据真正"有效" |
| Excel 写入被占用 | 提示关闭同名文件 | `500` `EXPORT_FAILED` |
| 导出器未知 / 用例集不存在 | 明确错误码 | `404` `NOT_FOUND` |
| 未实现（V2.0/V3.0）能力被调用 | 显式版本说明，而非静默 404 | `501` `FEATURE_NOT_AVAILABLE` |

---

## 八、测试

```bash
python -m pytest              # 126 项，覆盖解析/设计/优化/LLM/导出/接口
python -m pytest --cov=app    # 需要 pytest-cov
```

测试特点：

- 全程**无网络**：LLM 通过 `httpx.AsyncClient` 替身 + `FakeProvider` 打桩；
- 全程**无污染**：`conftest.py` 在导入任何 `app` 模块前把 `STORAGE_DIR` 指向临时目录；
- 覆盖异常路径：非法 JSON、超时、401、字段缺失、空文档、未知格式、501 占位。

---

## 九、功能自测清单

**环境与启动**
- [ ] `pip install -r requirements.txt` 成功
- [ ] 复制 `.env.example` 为 `.env` 后 `python run.py` 启动无报错
- [ ] 打开 http://127.0.0.1:8000/docs 可见全部接口
- [ ] `python -m pytest` 全部通过

**大模型配置（v1.1.0 新增）**
- [ ] `/health` 返回 `llm_source=env`，表示默认使用 `.env` 基线
- [ ] 「运行状态 → 大模型配置」能读到当前厂商 / 模型与掩码 Key（不回显明文）
- [ ] 切换厂商后自动带出默认模型 / 端点，可「拉取模型」或直接输入自定义模型名
- [ ] 「测试连接」返回 `ok=true` 与耗时；Key / 端点错误时给出可读失败原因
- [ ] 保存后 `/health` 的 `llm_source` 变为 `runtime`，无需重启即可用于解析 / 生成
- [ ] 「恢复 .env 配置」后 `llm_source` 回到 `env`，且覆盖文件被删除
- [ ] 缺少必填项（如 OpenAI 兼容端点未填 base_url）时红色提示并禁用保存

**文档上传与解析**
- [ ] 上传 `.md` / `.txt` 成功并返回 `doc_id` 与预览
- [ ] 上传 `.docx`（含字段说明表格）成功，字段约束被正确识别
- [ ] 上传 `.pdf`（文本型）成功；上传扫描件 PDF 返回可读错误提示
- [ ] 上传 `.xlsx` 返回 `415` 且提示支持格式列表
- [ ] 上传 GBK 编码的 `.txt` 中文不乱码，并出现编码告警

**需求解析**
- [ ] 未配置 `LLM_API_KEY` 时 `/health` 显示 `llm_available=false` 与降级原因
- [ ] 粘贴需求文本调用 `/requirements/parse` 返回结构化 `items`
- [ ] 字段的 min/max、长度、枚举、必填被正确抽取
- [ ] 「长度 2~20」被解析为长度约束（`min_length/max_length`），而非数值区间
- [ ] 「11位数字」字段解析为字符串类型但保留 `value_charset=digits`
- [ ] 从 Word/网页复制粘贴的 Tab 分隔表格（含表头）能被识别为字段表格
- [ ] Tab 表格抽不出字段时出现可操作告警，而不是静默丢失约束
- [ ] 主流程 / 备选流程 / 异常场景 / 业务规则 / 验收标准分类正确
- [ ] 配置 `LLM_API_KEY` 后 `parse_meta.provider` 变为 `deepseek`

**用例生成**
- [ ] 三种方法可单独勾选或组合使用
- [ ] 边界值包含 `最小值-1 / 最小值 / 最小值+1 / 最大值-1 / 最大值 / 最大值+1`
- [ ] 等长字段（如「6位验证码」）的 5 位与 7 位数据均被判为异常用例，6 位为边界用例
- [ ] 等价类包含有效类与无效类（含必填留空）
- [ ] 场景法产出主流程、备选流、异常场景、业务规则用例
- [ ] 重复用例被去重，编号形如 `TC-EQ-001 / TC-BV-001 / TC-SC-001`
- [ ] 同一必填字段的「留空」用例在等价类与边界值之间只保留一条，且「覆盖方法」列显示两种方法
- [ ] 场景法用例（无测试数据）不会被互相误合并
- [ ] 不同需求条目下的同数据用例不会被误合并
- [ ] 「11位数字」类字段的测试数据是数字（如 `11111111111`），不是 `AAAAAAAAAAA`
- [ ] 手机号字段的有效等价类数据满足 `^1[3-9]\d{9}$`（如 `13800138000`）
- [ ] 传入 `decision_table` 返回 `501` 且提示 V2.0

**导出**
- [ ] `/export` 返回 xlsx，文件名含中文且可正常下载
- [ ] Excel 含「测试用例 / 用例统计 / 需求追溯 / 生成信息」4 个表
- [ ] 「用例统计」区分「需求解析方式」与「用例生成方式」；「生成信息」区分两阶段的 Provider 与是否使用 LLM
- [ ] 未启用的 Provider 显示为「未启用（本次仅使用规则引擎）」，不出现"Provider=deepseek 但未使用 LLM"的矛盾展示
- [ ] 用例标题、步骤、预期结果换行展示正常，表头冻结、支持筛选
- [ ] 「覆盖方法」列对跨方法合并的用例显示多种方法（如「等价类划分、边界值分析」）
- [ ] JSON 导出的结构可被 `json.loads` 正确解析

**健壮性**
- [ ] 缺少 `doc_id` 与 `text` 时返回 `400` 且提示明确
- [ ] 不存在的 `suite_id` 返回 `404`
- [ ] 大文档触发 `MAX_CASES_PER_REQUIREMENT` 截断并告警

---

## 十、路线图（V2.0 / V3.0 / V4.0，架构已预留）

> 完整路线图与状态见 [ROADMAP.md](ROADMAP.md)；分支模型与发版流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。
> 以下为规划摘要，接口抽象已就绪，扩展时无需改动主干。

**V2.0 —— 设计方法补全与工程化**

- 设计策略：判定表、因果图、正交实验（`app/design/v2_strategies.py` 已占位，501 提示已就绪）
- 导出格式：XMind、CSV、TestLink XML（注册表 + 抽象已就绪）
- 需求侧：需求变更差异对比、需求-用例双向追溯矩阵
- 覆盖率：字段/边界/规则维度的覆盖率分析与缺口提示
- 存储：SQLAlchemy 持久化 + 用例版本管理（替换 `JsonObjectStore`）
- 解析：扫描件 PDF OCR、Excel 需求清单解析（新增 `DocumentParser` 子类）

**V3.0 —— AI 测试平台化**

- 外部集成：禅道 / Jira 双向同步（`ExternalSyncAdapter` 已定义，含占位实现）
- 多 Provider 路由：按任务类型/成本/质量自动选择模型，Prompt 版本化管理与回归评测
- 用例执行联动：对接自动化框架，回写执行结果，形成"生成 → 执行 → 反馈优化"闭环
- 知识沉淀：历史用例向量召回，减少重复生成并提升一致性
- 多租户与权限：项目隔离、配额与审计日志

**V4.0 —— 智能化与生态（方向性规划）**

- 多智能体协作：需求评审员 / 用例设计员 / 评审员协同，自动发现需求歧义与缺口
- 质量度量与生态开放：缺陷预测、用例有效性回评；插件市场 / SDK、开放 REST + Webhook
- 多模态与私有化：原型图 / 流程图 / OpenAPI 直接生成用例；全离线大模型一键部署包

---

## 十一、常见问题（FAQ）

**Q1：浏览器访问 `http://0.0.0.0:8000/` 返回 `502 Bad Gateway`，网络面板里「远程地址」是 `127.0.0.1:789x`。**

这不是服务故障，而是请求被**本地代理**（Clash / V2Ray / 公司代理，789x 是其混合端口）拦截了。
服务日志会正常显示 `Application startup complete`，且用 `curl` 直连是通的：

```bash
curl --noproxy "*" http://127.0.0.1:8000/api/v1/health
```

解决方式（任选其一）：

1. 地址改为 `http://127.0.0.1:8000/` 或 `http://localhost:8000/`；
2. 在代理软件里把 `127.0.0.1`、`localhost`、`0.0.0.0` 加入「绕过代理 / Bypass」列表；
3. Windows「设置 → 网络和 Internet → 代理」中勾选"请勿对本地地址使用代理服务器"；
4. 临时关闭系统代理后再访问。

**Q2：`/health` 显示 `llm_available=false`，或解析结果 `provider=rule`。**

表示当前走的是纯规则引擎。检查 `.env` 中 `LLM_API_KEY` 是否填写、
`LLM_PROVIDER` 是否为 `deepseek`（或 `openai_compatible` 且 `LLM_BASE_URL` 正确）。
`detail` / `parse_meta.fallback_reason` 里会写明具体降级原因（未配置密钥 / 超时 / HTTP 401 等）。

**Q3：上传 `.docx` 或 `.pdf` 报"缺少依赖"。**

按提示安装即可：`pip install python-docx pypdf`。若公司网络受限，可先另存为 `.txt`/`.md` 再上传
（解析链路与后续设计流程完全一致）。

**Q4：PDF 上传成功但提示"未抽取到有效文本"。**

该 PDF 是扫描件/图片型，`pypdf` 只能抽取文本型 PDF。V1.0 不含 OCR，
可先用任意 OCR 工具转成文本，或把需求整理为 Markdown 再上传。

**Q5：报 `LLM_RESPONSE_INVALID`。**

模型连续多次未返回合法 JSON。系统已内置修复（剥离代码块、去注释、去尾逗号、中文引号）与重试；
仍失败时可调低 `LLM_TEMPERATURE`、换用 `deepseek-chat`，或降低 `max_items` 让输出更短。

**Q6：报 `EXPORT_FAILED`。**

最常见原因是本地已打开同名 Excel 文件导致写入被占用，请关闭后重试。
导出文件同时会在 `storage/exports/` 归档一份，可直接取用。

**Q7：报 `501 FEATURE_NOT_AVAILABLE`。**

说明调用了 V2.0/V3.0 预留能力（判定表 / 因果图 / 正交实验 / 禅道同步等），
接口已登记但未实现。V1.0 请使用 `equivalence` / `boundary` / `scenario`。

**Q8：用例数量太多或太少。**

- 太多：调小 `MAX_CASES_PER_REQUIREMENT`，或只勾选部分设计方法；
- 太少：多为文档结构过于松散，可启用 LLM 解析（`use_llm=true`），
  并把文档整理为「Markdown 标题 + 字段约束表格 + 主流程/异常场景列表」。

**Q9：为什么结果里同一个测试点（如"必填字段留空"）只出现一条用例？**

这是**去重剔除**在生效，不是漏生成。去重分两层：

1. **精确指纹**（设计方法 + 标题 + 测试数据）：同一策略重复产出时去掉；
2. **语义重叠**（同模块 + 同用例类型 + 完全相同的测试数据 + 需求范围相交）：
   等价类与边界值经常对同一个测试点各产一条，例如必填字段留空，
   等价类叫「无效等价类（必填字段留空）」，边界值叫「必填边界（留空）」，
   测试数据都是 `{"字段": ""}` —— 这类会合并为一条，并在**覆盖方法**列记录
   「等价类划分、边界值分析」，说明该用例由两种方法共同覆盖，信息没有丢。

结果页指标「去重剔除」即为第二类合并掉的条数；Excel 的「测试用例」页有独立
「覆盖方法」列，JSON 对应 `covered_methods` 字段。

注意：场景法用例的 `test_data` 为空且一条用例覆盖整条流程，因此**不参与**第 2 层合并，
不会被误并成一条；用例类型不同（正常 vs 异常）的用例也不会合并，以免污染类型统计。

**Q10：结果页「需求条目」「覆盖需求」为什么总是同一个数字（例如一直是 3）？**

这两个指标都是**实时计算**的，不存在写死：`需求条目` = 文档解析出的章节数，
`覆盖需求` = 至少生成 1 条用例的条目数。它们一直相同，通常是因为你反复用了同一份
默认示例需求（`examples/sample_requirement.md` 已扩充为 5 个章节，便于区分）。
若二者小于文档章节数，请看告警：可能是触发了 `max_items` 上限，或某些条目没解析出可测字段。
把鼠标悬停在指标上可看到具体口径说明。

**Q11：为什么「需求解析」显示 LLM，「用例生成」却显示规则引擎？**

这是**两段式链路的正常设计**，不是 Bug：需求解析负责"读懂文档"（建议开启 LLM），
用例生成用确定性规则引擎即可覆盖等价类/边界值（更省钱、更稳定）。
界面现在把两阶段分开显示，可用「生成阶段也调用大模型」开关单独启用生成阶段的 LLM 增强。
若两者都显示规则引擎，说明 `LLM_API_KEY` 未配置或调用失败（见 `parse_meta.fallback_reason`）。

**Q12：为什么数字字段的测试数据变成了 `AAAAAAAAAAA`？**

这是已修复的缺陷：长度类字段（如「11位数字」「6位验证码」）此前统一用字母 `A` 填充，
产出违反字段自身约束的数据。现在解析器会保留「数字串」语义（`value_charset=digits`），
数据构造自动改用数字填充；手机号/身份证等内置格式字段还会直接给出符合正则的样例值。
若你仍看到字母数据，请确认该字段的约束文本里是否含"数字/号码"等字样，或把原始约束发给开发者复核。

**Q13：测试报 `pytest-asyncio` 相关错误。**

本项目的异步测试依赖它，请安装开发依赖：`pip install -r requirements-dev.txt`。

---

## 十二、假设与限制（显式声明）

1. **PDF 仅支持文本型**：`pypdf` 无法抽取扫描件文字，本版本不做 OCR；
   替代方案：安装 `pdfplumber` 新增解析器，或先转换为文本再上传。
2. **规则解析对文档结构敏感**：Markdown 标题 + 字段表格的文档效果最佳；
   结构松散时建议启用 LLM 解析，准确率差异明显。
   表格支持 Markdown（`| 列 |`）、`.docx` 原生表格与 Tab 分隔（需含表头）；
   纯空格对齐的表格（如从 PDF 复制的固定宽度表格）仍可能识别失败，此时会给出告警。
3. **未使用数据库**：V1.0 以 JSON 文件落盘（单机、可读、零依赖），不适合多实例并发部署。
4. **未做鉴权**：接口默认开放、CORS 放开，适合内网/本地使用；生产部署前需自行加认证。
5. **LLM 输出需人工复核**：LLM 增强用例统一打上 `LLM增强 / 需复核` 标签，不会与规则用例混淆。
6. **未内置第三方 SDK**：DeepSeek 通过 OpenAI 兼容 HTTP 协议直连（`httpx`），不依赖 `openai` 包；
   如官方接口协议变更，只需调整 `openai_compatible.py`。
7. **前端需要构建**：界面是 Vue 3 + TypeScript 单页应用，修改 `frontend/src/**` 后须执行 `cd frontend && npm run build`
   重新产出 `app/static/`；后端运行本身不依赖 Node.js，仓库已包含构建产物。

---

## 十三、免责与合规

- 请勿将生产环境密钥提交到代码仓库，`LLM_API_KEY` 仅通过环境变量注入；
- 上传的需求文档会落盘到 `STORAGE_DIR`，请按企业数据安全要求选择存储位置与清理策略。

---

## 十四、许可证与参与贡献

- **许可证**：[MIT License](LICENSE)。可自由用于商业与非商业场景，请保留版权声明。
- **贡献指南**：[CONTRIBUTING.md](CONTRIBUTING.md) —— 开发环境、分支模型（为 V2.0/V3.0/V4.0 预留）、
  提交规范与发版 Checklist。
- **安全策略**：[SECURITY.md](SECURITY.md) —— 漏洞上报渠道与**部署前必读的安全清单**
  （接口无鉴权、CORS 放开、文档外发第三方 LLM 等）。
- **行为准则**：[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。
- **更新日志**：[CHANGELOG.md](CHANGELOG.md)。
