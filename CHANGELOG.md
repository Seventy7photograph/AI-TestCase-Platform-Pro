# 更新日志

本文件记录本项目的所有重要变更。
格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Fixed

- **设计引擎**：修复「有效等价类 / 边界内」测试数据违反字段自身约束的问题：
  - 长度类字段（如手机号「11 位数字」）在内置样例长度与目标长度不一致时不再复用样例，
    避免 min-1 / min / min+1 / max-1 / max / max+1 六个边界点塌缩成同一个值；
  - 数值区间代表值改为整数中点或按字段精度对齐，修复「查询页码 1~1000」产出 `500.5`、
    「订单金额」产出 `25000.005` 这类非法数据；
  - 布尔字段不再生成无意义的「全空格边界」用例。
- **API**：`POST /requirements/{doc_id}/testcases` 的 `methods` / `use_llm_in_design`
  由请求体改为查询参数，修复前端传入的设计方法被静默忽略、始终按全部方法生成的问题。

### Changed

- **模块归属**：容器型一级标题（如「某某系统需求说明书」）或空标题不再退化成所有用例的
  模块名；无一级标题时按章节标题归属，「所属模块」列恢复可读。
- **用例统计**：新增「按设计方法（含合并覆盖）」维度，跨方法合并的用例不再被少算；
  Excel 统计页与前端「覆盖方法」卡片同步展示。
- **生成元数据**：`generation_meta.llm_used` 仅在确有 LLM 用例产出时为真，不再因
  「尝试调用但失败」而误报。
- **单条需求用例上限**：`MAX_CASES_PER_REQUIREMENT` 改为按「需求条目」而非
  「条目 × 方法」计数，避免多方法叠加后总量失控。
- **文档摘要**：`/documents` 返回新增 `encoding` 字段，前端文档库与预览同步展示。

### Added

- **前端反馈层**：新增统一 `useNotice` 提示组件（顶部墨条 toast / 右下角通知 / 确认弹框），
  为上传、解析、生成、导出、复制、刷新等操作补齐成功 / 失败 / 警告提示，并在生成、
  重新解析、导出等耗时或覆盖性操作前增加二次确认。
- **可发现性**：为禁用按钮、V2 预留方法、状态徽标、密度切换、导出按钮等补充鼠标悬停
  提示；对未选择设计方法、无法生成等情况增加红色提示文案。

## [1.0.0] - 2026-10-04

首个正式版本：基于 Python + FastAPI 的 AI 测试用例生成助手，单机开箱即用。

### Added

- **文档解析**：支持 `.docx` / `.pdf` / `.txt` / `.md` / `.csv` / `.json`，兼容 GBK 等中文编码，
  Word 表格结构化平铺；解析器抽象 + 注册表。
- **需求结构化**：LLM 结构化抽取与规则引擎双路解析，未配置密钥或调用失败时自动降级并显式告警。
- **测试设计引擎**：等价类划分、边界值分析（min-1/min/min+1/max-1/max/max+1）、
  场景法（主流程 / 备选流 / 异常流 / 业务规则）；策略注册表 + 逐条需求调度。
- **用例优化**：两层去重（精确指纹 + 跨方法语义重叠）、优先级排序、按设计方法自动编号（TC-EQ/BV/SC）。
- **导出**：Excel（用例明细 / 用例统计 / 需求追溯 / 生成信息 四个 Sheet）与 JSON。
- **Web 界面**：Vue 3 + TypeScript + Vite + Element Plus 单页应用，构建产物随仓库提供。
- **统一异常出口**：所有错误返回 `{success, code, message, detail}`。
- **扩展点预留**：设计策略、导出器、LLM Provider、外部集成（禅道/Jira）四类抽象接口。
- **测试**：覆盖解析器、规则引擎、设计策略、导出器、LLM Provider 与 API 端到端。

### Security

- `LLM_API_KEY` 等敏感配置仅通过环境变量注入，`.env` 已由 `.gitignore` 排除。
- 持久化层对资源 ID 做白名单校验，杜绝路径穿越；静态文件服务校验目录边界。

### Known Limitations

- 无鉴权、CORS 默认放开，仅适合本地 / 内网使用（详见 [SECURITY.md](SECURITY.md)）。
- 使用 JSON 文件存储，不适合多实例并发部署。
- PDF 仅支持文本型，暂不做 OCR。

[Unreleased]: https://github.com/Seventy7photograph/AI-TestCase-Platform-Pro/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Seventy7photograph/AI-TestCase-Platform-Pro/releases/tag/v1.0.0
