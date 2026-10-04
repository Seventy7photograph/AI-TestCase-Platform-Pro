export interface ApiResponse<T> {
  success: boolean;
  code: string;
  message: string;
  data: T | null;
}

export type DesignMethod =
  | "equivalence"
  | "boundary"
  | "scenario"
  | "decision_table"
  | "cause_effect"
  | "orthogonal";

export type Priority = "P0" | "P1" | "P2" | "P3";

export type CaseType =
  | "功能"
  | "边界"
  | "异常"
  | "场景"
  | "安全"
  | "性能"
  | "兼容性";

export interface FieldConstraint {
  name: string;
  label: string;
  data_type: string;
  required: boolean;
  nullable: boolean;
  min_value: number | null;
  max_value: number | null;
  min_length: number | null;
  max_length: number | null;
  enum_values: string[];
  pattern: string | null;
  default: string | null;
  unit: string | null;
  description: string;
}

export interface RequirementItem {
  id: string;
  title: string;
  module: string;
  description: string;
  priority: Priority;
  requirement_type: string;
  fields: FieldConstraint[];
  business_rules: string[];
  preconditions: string[];
  main_flow: string[];
  alternative_flows: string[];
  exceptions: string[];
  acceptance_criteria: string[];
  source_ref: string;
  raw_text: string;
}

export interface ParseMeta {
  provider: string;
  model: string;
  llm_used: boolean;
  fallback_used: boolean;
  fallback_reason: string;
  attempts: number;
  elapsed_ms: number;
  item_count: number;
  warnings: string[];
}

export interface RequirementDoc {
  doc_id: string;
  title: string;
  source_file: string;
  source_type: string;
  version: string;
  summary: string;
  items: RequirementItem[];
  created_at: string;
  parse_meta: ParseMeta;
}

export interface TestStep {
  no: number;
  action: string;
  expected: string;
}

export interface TestCase {
  case_id: string;
  title: string;
  module: string;
  requirement_ids: string[];
  design_method: DesignMethod;
  case_type: CaseType;
  priority: Priority;
  preconditions: string[];
  steps: TestStep[];
  expected_result: string;
  test_data: Record<string, string>;
  tags: string[];
  remarks: string;
  source: string;
  checksum: string;
  covered_methods: DesignMethod[];
}

export interface SuiteStats {
  total: number;
  duplicate_removed: number;
  by_method: Record<string, number>;
  /** 合并用例按「覆盖到的全部方法」重新计数，避免跨方法合并后被少算。 */
  by_covered_method: Record<string, number>;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
  requirement_coverage: Record<string, number>;
}

export interface GenerationMeta {
  methods: string[];
  llm_used: boolean;
  llm_provider: string;
  llm_model: string;
  fallback_used: boolean;
  warnings: string[];
  elapsed_ms: number;
}

export interface TestCaseSuite {
  suite_id: string;
  doc_id: string;
  doc_title: string;
  methods: DesignMethod[];
  cases: TestCase[];
  stats: SuiteStats;
  generation_meta: GenerationMeta;
  parse_meta: ParseMeta;
  created_at: string;
}

export interface DocumentSummary {
  doc_id: string;
  filename: string;
  extension: string;
  size_bytes: number;
  char_count: number;
  line_count: number;
  encoding: string;
  parser: string;
  page_count: number | null;
  table_count: number;
  warnings: string[];
  created_at: string;
  preview: string;
}

export interface MethodInfo {
  name: string;
  label: string;
  implemented: boolean;
  description: string;
}

export interface ExportFormatInfo {
  name: string;
  label: string;
  media_type: string;
  extension: string;
}

export interface HealthInfo {
  app_name: string;
  version: string;
  status: string;
  llm_provider: string;
  llm_model: string;
  llm_base_url: string;
  llm_available: boolean;
  llm_degraded_reason: string;
  /** env=来自 .env 基线；runtime=被「大模型配置」界面覆盖 */
  llm_source: string;
  methods: MethodInfo[];
  export_formats: ExportFormatInfo[];
  supported_extensions: string[];
}

export interface LLMModelOption {
  value: string;
  label: string;
  base_url: string;
}

export interface LLMProviderOption {
  name: string;
  label: string;
  description: string;
  requires_key: boolean;
  requires_base_url: boolean;
  allow_custom_model: boolean;
  default_base_url: string;
  default_model: string;
  models: LLMModelOption[];
}

export interface LLMConfigInfo {
  provider: string;
  model: string;
  base_url: string;
  api_key_configured: boolean;
  api_key_masked: string;
  timeout: number;
  max_retries: number;
  temperature: number;
  max_tokens: number;
  available: boolean;
  degraded_reason: string;
  /** env=来自 .env 基线；runtime=被界面覆盖 */
  source: string;
  overridden_fields: string[];
  env_defaults: Record<string, unknown>;
  providers: LLMProviderOption[];
}

export interface LLMConfigPayload {
  provider?: string;
  model?: string;
  base_url?: string;
  /** 省略=沿用现有 Key；空字符串=清除已保存的 Key */
  api_key?: string;
  timeout?: number;
  max_retries?: number;
  temperature?: number;
  max_tokens?: number;
}

export interface LLMTestResult {
  ok: boolean;
  provider: string;
  model: string;
  elapsed_ms: number;
  message: string;
  reply: string;
}

export interface LLMModelList {
  source: string;
  message: string;
  models: LLMModelOption[];
}

export interface IntegrationInfo {
  name: string;
  label: string;
  implemented: boolean;
}

export interface GenerateResult {
  requirement_doc: RequirementDoc;
  suite: TestCaseSuite;
  warnings: string[];
}
