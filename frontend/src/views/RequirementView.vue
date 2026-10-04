<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "@/api";
import type { FieldConstraint, RequirementItem } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { confirmAction, notice } from "@/composables/useNotice";
import {
  RESERVED_METHODS,
  V1_METHODS,
  dataTypeLabel,
  formatDateTime,
  formatDuration,
  methodLabel,
  requirementTypeLabel,
} from "@/utils/labels";
import EmptyState from "@/components/EmptyState.vue";
import ErrorNote from "@/components/ErrorNote.vue";
import PageHead from "@/components/PageHead.vue";
import PriorityMark from "@/components/PriorityMark.vue";
import StatStrip from "@/components/StatStrip.vue";
import type { StatItem } from "@/components/StatStrip.vue";

const route = useRoute();
const router = useRouter();
const docId = computed(() => String(route.params.docId ?? ""));

const requirement = useAsync((id: string) => api.requirement(id));
const generating = ref(false);
const methods = ref<string[]>([...V1_METHODS]);
const useLlmInDesign = ref(false);

const data = computed(() => requirement.data.value);

const statItems = computed<StatItem[]>(() => {
  const doc = data.value;
  if (!doc) return [];
  const meta = doc.parse_meta;
  const fieldCount = doc.items.reduce((sum, item) => sum + item.fields.length, 0);
  return [
    { label: "需求条目", value: doc.items.length, hint: "从文档中解析出的章节数量" },
    { label: "字段约束", value: fieldCount, hint: "等价类与边界值分析的输入数量" },
    {
      label: "解析口径",
      value: meta.llm_used ? `LLM · ${meta.provider}` : "规则引擎",
      tone: meta.fallback_used ? "warn" : "default",
      hint: meta.fallback_used
        ? `已降级：${meta.fallback_reason || "未配置或调用失败"}`
        : `${meta.model || "规则解析"}`,
    },
    { label: "解析耗时", value: formatDuration(meta.elapsed_ms), hint: `尝试 ${meta.attempts} 次` },
    { label: "解析时间", value: formatDateTime(doc.created_at), hint: doc.source_file || "来源：粘贴文本" },
  ];
});

function fieldConstraintText(field: FieldConstraint): string {
  const parts: string[] = [];
  if (field.required) parts.push("必填");
  if (field.enum_values?.length) parts.push(`取值 ${field.enum_values.join(" / ")}`);
  if (field.min_value !== null || field.max_value !== null) {
    parts.push(`范围 ${field.min_value ?? "不限"}~${field.max_value ?? "不限"}${field.unit ?? ""}`);
  }
  if (field.min_length !== null || field.max_length !== null) {
    parts.push(`长度 ${field.min_length ?? "-"}~${field.max_length ?? "-"}`);
  }
  if (field.pattern) parts.push(`格式 ${field.pattern}`);
  return parts.join("，") || field.description || "—";
}

function flowGroups(item: RequirementItem) {
  return [
    { key: "main", label: "主流程", values: item.main_flow },
    { key: "alt", label: "备选流程", values: item.alternative_flows },
    { key: "exc", label: "异常场景", values: item.exceptions },
    { key: "rule", label: "业务规则", values: item.business_rules },
    { key: "pre", label: "前置条件", values: item.preconditions },
    { key: "ac", label: "验收标准", values: item.acceptance_criteria },
  ].filter((group) => group.values.length > 0);
}

async function generateCases(): Promise<void> {
  if (!methods.value.length) {
    notice.error("请至少选择一种设计方法。");
    return;
  }
  if (useLlmInDesign.value) {
    const ok = await confirmAction(
      "生成阶段将调用大模型补齐场景用例，耗时更长。是否继续？",
      "开始生成用例",
      "开始生成",
    );
    if (!ok) return;
  }
  generating.value = true;
  try {
    const suite = await api.generateFromRequirement(
      docId.value,
      methods.value,
      useLlmInDesign.value,
    );
    notice.done("用例生成完成", `已生成 ${suite.stats.total} 条用例，正在打开用例集…`);
    await router.push(`/suites/${suite.suite_id}`);
  } catch (err) {
    notice.error(err, "生成失败，请稍后重试。");
  } finally {
    generating.value = false;
  }
}

async function reparse(): Promise<void> {
  if (!data.value) return;
  const ok = await confirmAction(
    `将重新解析《${data.value.title}》，这会覆盖当前的结构化需求。是否继续？`,
    "重新解析",
    "重新解析",
  );
  if (!ok) return;
  const result = await requirement.run(docId.value);
  if (result) {
    notice.success(`已重新解析，共 ${result.items.length} 条需求。`);
  } else if (requirement.error.value) {
    notice.error(requirement.error.value);
  }
}

onMounted(() => {
  void requirement.run(docId.value);
});
</script>

<template>
  <div class="stack">
    <PageHead
      :title="data?.title || '结构化需求'"
      :note="data ? `${data.doc_id} · 来源 ${data.source_file || '粘贴文本'} · 版本 ${data.version}` : '正在载入…'"
      back-to="/documents"
      back-label="文档与需求"
    >
      <template #actions>
        <el-button
          :disabled="!data"
          title="按当前解析设置重新解析本文档，会覆盖已保存的结构化需求"
          @click="reparse"
        >
          重新解析
        </el-button>
        <el-button
          type="primary"
          :loading="generating"
          :disabled="!data || !data.items.length"
          title="基于当前需求与所选设计方法生成用例集"
          @click="generateCases"
        >
          基于该需求生成用例
        </el-button>
      </template>
    </PageHead>

    <ErrorNote :error="requirement.error.value" />

    <el-skeleton v-if="requirement.loading.value && !data" :rows="6" animated class="pad" />

    <EmptyState
      v-else-if="!data"
      title="这份文档还没有结构化需求"
      hint="回到文档库，对目标文档点击「解析需求」，解析完成后即可在这里查看字段约束与业务流程。"
    >
      <el-button type="primary" @click="router.push('/documents')">去文档库</el-button>
    </EmptyState>

    <template v-else>
      <StatStrip :items="statItems" />

      <section class="card">
        <div class="card__head">
          <span class="card__title">生成设置</span>
          <span class="dim gen__note">对整份文档生效</span>
        </div>
        <div class="card__body row row--wrap">
          <el-checkbox-group v-model="methods">
            <el-checkbox v-for="method in V1_METHODS" :key="method" :value="method">
              {{ methodLabel(method) }}
            </el-checkbox>
            <el-checkbox
              v-for="method in RESERVED_METHODS"
              :key="method"
              :value="method"
              disabled
              title="该设计方法计划在 V2.0 提供，当前版本调用会返回 501"
            >
              {{ methodLabel(method) }}
              <span class="reserved">V2 预留</span>
            </el-checkbox>
          </el-checkbox-group>
          <span class="spacer"></span>
          <label class="inline" title="开启后会调用大模型补齐场景法用例，耗时更长">
            <el-switch v-model="useLlmInDesign" />
            <span>生成阶段也调用大模型</span>
          </label>
          <p v-if="!methods.length" class="hint hint--bad">请至少选择一种设计方法。</p>
        </div>
      </section>

      <article v-for="item in data.items" :key="item.id" class="card">
        <div class="card__head">
          <div class="row row--wrap item__head">
            <span class="stamp">{{ item.id }}</span>
            <h2 class="item__title">{{ item.title }}</h2>
            <span class="chip mono">{{ item.module }}</span>
            <span class="chip">{{ requirementTypeLabel(item.requirement_type) }}</span>
            <PriorityMark :value="item.priority" show-label />
          </div>
        </div>

        <div class="card__body stack stack--tight">
          <p v-if="item.description" class="item__desc">{{ item.description }}</p>

          <div v-if="item.fields.length" class="block">
            <p class="label">字段约束</p>
            <table class="fields">
              <thead>
                <tr>
                  <th scope="col">字段</th>
                  <th scope="col">类型</th>
                  <th scope="col">约束</th>
                  <th scope="col">说明</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="field in item.fields" :key="field.name">
                  <td class="fields__name">{{ field.label || field.name }}</td>
                  <td class="fields__type">{{ dataTypeLabel(field.data_type) }}</td>
                  <td>{{ fieldConstraintText(field) }}</td>
                  <td class="dim">{{ field.description || "—" }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="grid grid--2">
            <div v-for="group in flowGroups(item)" :key="group.key" class="block">
              <p class="label">{{ group.label }}</p>
              <ol class="flow">
                <li v-for="(line, index) in group.values" :key="index">{{ line }}</li>
              </ol>
            </div>
          </div>

          <details v-if="item.raw_text" class="raw">
            <summary>查看原文片段</summary>
            <pre class="pre">{{ item.raw_text }}</pre>
          </details>
        </div>
      </article>
    </template>
  </div>
</template>

<style scoped>
.pad {
  padding: var(--s5);
}

.gen__note,
.item__desc {
  font-size: var(--fs-xs);
}

.hint {
  font-size: var(--fs-xs);
  line-height: 1.55;
}

.hint--bad {
  color: var(--danger);
}

.item__desc {
  font-size: var(--fs-sm);
  color: var(--ink-2);
}

.item__head {
  gap: var(--s2);
}

.item__title {
  font-size: var(--fs-md);
  font-weight: 600;
  letter-spacing: -0.01em;
}

.chip {
  font-size: 10px;
  color: var(--ink-3);
  border: 1px solid var(--rule-strong);
  border-radius: var(--radius-sm);
  padding: 0 4px;
}

.reserved {
  margin-left: 4px;
  font-size: 10px;
  color: var(--ink-4);
  border: 1px solid var(--rule-strong);
  border-radius: var(--radius-sm);
  padding: 0 4px;
}

.inline {
  display: inline-flex;
  align-items: center;
  gap: var(--s2);
  font-size: var(--fs-base);
  color: var(--ink-2);
  cursor: pointer;
}

.block .label {
  display: block;
  margin-bottom: 6px;
}

.fields {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-sm);
  background: var(--card);
  border: 1px solid var(--rule);
  border-radius: var(--radius);
}

.fields th {
  text-align: left;
  font-size: var(--fs-xs);
  letter-spacing: var(--tracking-label);
  text-transform: uppercase;
  color: var(--ink-3);
  background: var(--paper-sunk);
  padding: 6px 10px;
  border-bottom: 1px solid var(--rule);
  font-weight: 600;
}

.fields td {
  padding: 7px 10px;
  border-bottom: 1px solid var(--rule);
  vertical-align: top;
  color: var(--ink-2);
}

.fields tr:last-child td {
  border-bottom: 0;
}

.fields__name {
  color: var(--ink);
  font-weight: 500;
}

.fields__type {
  font-size: var(--fs-xs);
  color: var(--ink-3);
}

.flow {
  margin: 0;
  padding-left: 18px;
  font-size: var(--fs-sm);
  line-height: 1.7;
  color: var(--ink-2);
}

.raw {
  border-top: 1px solid var(--rule);
  padding-top: var(--s2);
}

.raw summary {
  font-size: var(--fs-xs);
  color: var(--ink-3);
  cursor: pointer;
}

.raw summary:hover {
  color: var(--stamp-deep);
}

.raw pre {
  margin: var(--s2) 0 0;
  padding: var(--s3);
  max-height: 260px;
  overflow: auto;
  font-family: var(--font-ui);
  font-size: var(--fs-xs);
  line-height: 1.7;
  color: var(--ink-2);
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: var(--radius-sm);
}
</style>
