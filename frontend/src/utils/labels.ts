import type { CaseType, DesignMethod, Priority } from "@/api";

export const METHOD_LABELS: Record<string, string> = {
  equivalence: "等价类划分",
  boundary: "边界值分析",
  scenario: "场景法",
  decision_table: "判定表",
  cause_effect: "因果图",
  orthogonal: "正交实验",
};

export const METHOD_SHORT: Record<string, string> = {
  equivalence: "等价类",
  boundary: "边界值",
  scenario: "场景法",
  decision_table: "判定表",
  cause_effect: "因果图",
  orthogonal: "正交实验",
};

export const METHOD_CODES: Record<string, string> = {
  equivalence: "EQ",
  boundary: "BV",
  scenario: "SC",
  decision_table: "DT",
  cause_effect: "CE",
  orthogonal: "OG",
};

export const V1_METHODS: DesignMethod[] = [
  "equivalence",
  "boundary",
  "scenario",
];

export const RESERVED_METHODS: DesignMethod[] = [
  "decision_table",
  "cause_effect",
  "orthogonal",
];

export const PRIORITY_ORDER: Priority[] = ["P0", "P1", "P2", "P3"];

export const CASE_TYPES: CaseType[] = [
  "功能",
  "边界",
  "异常",
  "场景",
  "安全",
  "性能",
  "兼容性",
];

export function methodLabel(value?: string): string {
  if (!value) return "—";
  return METHOD_LABELS[value] ?? value;
}

export function methodShort(value?: string): string {
  if (!value) return "—";
  return METHOD_SHORT[value] ?? value;
}

export function priorityRank(value: string): number {
  const index = PRIORITY_ORDER.indexOf(value as Priority);
  return index === -1 ? PRIORITY_ORDER.length : index;
}

export function formatBytes(size: number): string {
  if (!Number.isFinite(size) || size <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const exp = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  const value = size / 1024 ** exp;
  return `${exp === 0 ? value : value.toFixed(1)} ${units[exp]}`;
}

export function formatDuration(ms: number): string {
  if (!Number.isFinite(ms) || ms <= 0) return "—";
  if (ms < 1000) return `${Math.round(ms)} ms`;
  const seconds = ms / 1000;
  if (seconds < 60) return `${seconds.toFixed(1)} s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes} min ${Math.round(seconds % 60)} s`;
}

export function formatDateTime(iso: string): string {
  if (!iso) return "—";
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())} ${pad(
    parsed.getHours(),
  )}:${pad(parsed.getMinutes())}`;
}

export function percent(part: number, whole: number): string {
  if (!whole) return "—";
  return `${Math.round((part / whole) * 100)}%`;
}

export function caseToPlainText(item: {
  case_id: string;
  title: string;
  module: string;
  priority: string;
  case_type: string;
  design_method: string;
  preconditions: string[];
  steps: { no: number; action: string; expected: string }[];
  expected_result: string;
  test_data: Record<string, string>;
}): string {
  const lines: string[] = [
    `${item.case_id}　${item.title}`,
    `模块：${item.module}　优先级：${item.priority}　类型：${item.case_type}　方法：${methodLabel(item.design_method)}`,
  ];
  if (item.preconditions.length) {
    lines.push(`前置条件：${item.preconditions.join("；")}`);
  }
  if (Object.keys(item.test_data).length) {
    lines.push(
      `测试数据：${Object.entries(item.test_data)
        .map(([key, value]) => `${key}=${value === "" ? "(空)" : value}`)
        .join("；")}`,
    );
  }
  item.steps.forEach((step) => {
    lines.push(`${step.no}. ${step.action}${step.expected ? ` → 预期：${step.expected}` : ""}`);
  });
  if (item.expected_result) lines.push(`预期结果：${item.expected_result}`);
  return lines.join("\n");
}

export const REQUIREMENT_TYPE_LABELS: Record<string, string> = {
  functional: "功能",
  business_rule: "业务规则",
  interface: "接口",
  constraint: "约束",
  non_functional: "非功能",
};

export const DATA_TYPE_LABELS: Record<string, string> = {
  string: "字符串",
  integer: "整数",
  float: "小数",
  boolean: "布尔",
  enum: "枚举",
  date: "日期",
  datetime: "日期时间",
  other: "其它",
};

export function requirementTypeLabel(value?: string): string {
  if (!value) return "—";
  return REQUIREMENT_TYPE_LABELS[value] ?? value;
}

export function dataTypeLabel(value?: string): string {
  if (!value) return "—";
  return DATA_TYPE_LABELS[value] ?? value;
}