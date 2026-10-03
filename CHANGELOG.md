# 更新日志

本文件记录本项目的所有重要变更。
格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

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
