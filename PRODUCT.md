# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

现有后端：Python + FastAPI（`app/`），REST 前缀 `/api/v1`，统一响应体 `{success, code, message, detail}`，本地 JSON 文件持久化（`storage/`）。当前前端为单文件 `app/static/index.html`，由 FastAPI 挂载在 `/` 提供。

前端重构（用户 2026-10-03 明确指定）：**Vue 3 + TypeScript + Vite + Element Plus**，替换 `app/static/index.html`。设计基调由用户给定为「流畅好用、有质感、高级、简约」。本次属于**替换视觉世界**的重构：保留产品事实、内容、功能与接口契约，旧视觉仅作证据与反面参考。

## Users

- 主要用户：**测试工程师 / QA**。场景是拿到需求文档（Word / PDF / 粘贴文本）后，需要在一个工作时段内产出可评审、可执行、可导入用例管理工具的用例集。
- 次要用户：**产品经理 / 开发自测者**，需要快速核对需求覆盖度与边界条件是否被覆盖。
- 使用环境：本地或内网部署，桌面浏览器为主（≥1366px），偶发手机查看结果；中文界面。*（推断：来自 README 的「局域网访问」提示与部署方式）*

## Product Purpose

把非结构化需求文档转成**结构化需求模型（中间表示）**，再用等价类划分 / 边界值分析 / 场景法生成用例，经双层去重与优先级排序后导出 Excel 交付。

成功意味着：从文档到可交付用例集的时间由小时级降到分钟级；每条用例都能追溯到具体需求条目；**即使没有配置 LLM API Key，整条链路仍端到端可用**。

## Positioning

以**确定性规则引擎为骨干、LLM 仅作可选增强**，LLM 缺失或失败时显式降级并告警。相邻工具要么纯 LLM（不可控、不可离线、结果不稳定），要么纯模板（覆盖度低）。可验证的差异化机制：需求追溯（`requirement_ids` + 覆盖率统计）、双层去重（精确指纹 + 跨方法语义重叠并合并 `covered_methods`）、解析与生成两阶段的口径分离（`parse_meta` 与 `generation_meta` 独立记录是否使用 LLM）。

## Operating Context

- 输入物料：`.docx` / `.pdf` / `.txt` / `.md` / `.csv` / `.json`；Word 表格需保留列结构；兼容中文编码（含 GBK）。
- 交付物：Excel 四个 Sheet（用例明细 / 用例统计 / 需求追溯 / 生成信息），另有 JSON 导出。
- 下游习惯：用例字段对齐禅道 / Jira / XMind 通用导入模板；编号形如 `TC-EQ-001` / `TC-BV-001` / `TC-SC-001`。
- 引擎配置：DeepSeek（默认）或任意 OpenAI 兼容端点；`MAX_CASES_PER_REQUIREMENT=60` 用于抑制边界值爆炸。
- 持久化：本地 JSON 文件（`storage/data`、`storage/uploads`、`storage/exports`），无数据库。

## Capabilities and Constraints

已实现且端到端可用：文档上传与解析、需求结构化解析（LLM + 规则双路）、三类设计方法、用例去重与排序编号、Excel / JSON 导出、统一异常出口、健康检查与能力清单（`/health`、`/testcases/methods`、`/export/formats`、`/integrations`、`/documents`、`/requirements/*`、`/testcases/*`、`/pipeline/generate`）。

V2.0 / V3.0 已定义接口但调用返回 501：判定表、因果图、正交实验、XMind / CSV / TestLink 导出、Qwen / GLM / Ollama Provider、禅道 / Jira 同步。界面必须把这些**明确标注为未实现**，不得让用户误以为可用。

约束：REST 契约不可变更（前端只消费 `/api/v1` 现有端点）；上传上限 20MB；无鉴权、无多租户（单机工具）；`max_items` 上限 50；单条需求用例上限 60。

## Brand Commitments

- 产品名：**AI 测试用例生成助手**（内部标识 `AI-TestCase-Platform-Pro`）。
- 语言：中文为主；术语跟随国内测试工程习惯（等价类划分、边界值分析、场景法、用例集）。
- 用户给定的设计基调（binding）：**流畅好用、有质感、高级、简约**。

## Evidence on Hand

- `examples/sample_requirement.md`：真实可用的需求样例，用于演示生成链路。
- `examples/demo_offline.py`、`examples/acceptance_check.py`：离线演示与验收脚本，可产出真实用例数据。
- `storage/` 下已有历史生成的文档与用例集 JSON，可作为真实数据用于界面演示。
- **不可编造**：不得虚构客户名、案例、性能基准、价格，或宣称 V2/V3 集成已完成。

## Product Principles

1. **确定性优先**：规则引擎是主干，LLM 是可降级的增强；任何降级都必须在界面上被看见。
2. **可追溯**：每条用例都能回到它覆盖的需求条目；统计口径必须自解释，不用漂亮数字掩盖口径。
3. **交付物导向**：界面服务于「产出一份能直接交给下游的用例集」，而不是展示生成过程本身。
4. **密度即效率**：测试工程师需要一次看到大量字段，信息密度是功能而不是噪音。
5. **离线可用**：无网络、无 Key 时核心链路依然可用。

## Accessibility & Inclusion

- 中文界面需保证键盘可达（Tab 顺序、焦点可见）与表单错误可被读屏识别。
- 表格信息不得仅靠颜色区分优先级，需同时给出文字或形状标记。
- 目标对比度：正文与占位文本 ≥4.5:1，大号文本 ≥3:1。

## Open Decisions

- 是否需要登录 / 多用户（当前后端无鉴权）：本次按单机工具处理。
- 是否保留旧的单文件演示页：本次以 SPA 构建产物替换 `app/static/index.html`。
- 历史用例集的保留策略：后端 JSON 已存储，前端只读展示。
