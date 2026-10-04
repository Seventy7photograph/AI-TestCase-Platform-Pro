<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Download } from "@element-plus/icons-vue";

import { api, saveBlob } from "@/api";
import type { RequirementDoc, RequirementItem, TestCase, TestCaseSuite } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { notice } from "@/composables/useNotice";
import { formatDateTime, formatDuration, methodLabel, percent, priorityRank } from "@/utils/labels";
import CaseTable from "@/components/CaseTable.vue";
import EmptyState from "@/components/EmptyState.vue";
import ErrorNote from "@/components/ErrorNote.vue";
import PageHead from "@/components/PageHead.vue";
import PriorityMark from "@/components/PriorityMark.vue";
import StatStrip from "@/components/StatStrip.vue";
import type { StatItem } from "@/components/StatStrip.vue";

interface CoverageRow {
  item: RequirementItem;
  count: number;
  cases: TestCase[];
}

const route = useRoute();
const router = useRouter();
const suiteId = computed(() => String(route.params.suiteId ?? ""));

const suite = useAsync((id: string) => api.suite(id));
const requirement = ref<RequirementDoc | null>(null);
const requirementMissing = ref(false);
const focusedCase = ref<string | null>(null);
const exporting = ref<"excel" | "json" | "">("");

const data = computed<TestCaseSuite | null>(() => suite.data.value);

const itemsIndex = computed(() => {
  const map = new Map<string, RequirementItem>();
  requirement.value?.items.forEach((item) => map.set(item.id, item));
  return map;
});

const coverage = computed<CoverageRow[]>(() => {
  const doc = requirement.value;
  const current = data.value;
  if (!doc || !current) return [];
  return doc.items
    .map((item) => {
      const cases = current.cases.filter((testCase) =>
        testCase.requirement_ids.includes(item.id),
      );
      return { item, count: cases.length, cases };
    })
    .sort((a, b) => priorityRank(a.item.priority) - priorityRank(b.item.priority));
});

const maxCoverage = computed(() =>
  Math.max(1, ...coverage.value.map((row) => row.count)),
);

const uncovered = computed(() => coverage.value.filter((row) => row.count === 0));

const statItems = computed<StatItem[]>(() => {
  const current = data.value;
  if (!current) return [];
  const stats = current.stats;
  const parse = current.parse_meta;
  const generation = current.generation_meta;
  const covered = Object.keys(stats.requirement_coverage ?? {}).length;
  const totalItems = requirement.value?.items.length ?? 0;
  const items: StatItem[] = [
    { label: "用例总数", value: stats.total, hint: "去重合并后的最终条数" },
    {
      label: "去重剔除",
      value: stats.duplicate_removed,
      hint: "精确指纹与跨方法语义重叠合并掉的重复用例",
    },
    {
      label: "需求覆盖",
      value: totalItems ? `${covered} / ${totalItems}` : `${covered} 条`,
      tone: totalItems && covered < totalItems ? "warn" : "good",
      hint: totalItems
        ? `覆盖率 ${percent(covered, totalItems)}，未覆盖条目会在下方列出`
        : "至少生成 1 条用例的需求条目数",
    },
    {
      label: "解析口径",
      value: parse.llm_used ? `LLM · ${parse.provider}` : "规则引擎",
      tone: parse.fallback_used ? "warn" : "default",
      hint: parse.fallback_used
        ? `已降级：${parse.fallback_reason || "未配置或调用失败"}`
        : "需求解析阶段使用的引擎",
    },
    {
      label: "生成口径",
      value: generation.llm_used ? "LLM 增强" : "规则引擎",
      hint: generation.llm_used
        ? `${generation.llm_provider} · ${generation.llm_model}`
        : "设计方法生成用例时的引擎",
    },
    {
      label: "覆盖方法",
      value: Object.keys(stats.by_covered_method ?? {}).length,
      hint:
        Object.entries(stats.by_covered_method ?? {})
          .map(([name, count]) => `${name} ${count}`)
          .join(" · ") || "按用例实际覆盖的方法计数（含跨方法合并）",
    },
    { label: "生成耗时", value: formatDuration(generation.elapsed_ms), hint: "设计引擎耗时" },
  ];
  return items;
});

async function exportAs(format: "excel" | "json"): Promise<void> {
  const current = data.value;
  if (!current || exporting.value) return;
  exporting.value = format;
  try {
    const file = await api.exportSuite(current.suite_id, format);
    saveBlob(
      file.blob,
      file.filename || `${current.suite_id}.${format === "excel" ? "xlsx" : "json"}`,
    );
    notice.success(`已导出 ${format === "excel" ? "Excel" : "JSON"} 文件。`);
  } catch (err) {
    notice.error(err, "导出失败，请稍后重试。");
  } finally {
    exporting.value = "";
  }
}

async function load(): Promise<void> {
  requirement.value = null;
  requirementMissing.value = false;
  const current = await suite.run(suiteId.value);
  if (!current?.doc_id) return;
  try {
    requirement.value = await api.requirement(current.doc_id);
  } catch {
    requirementMissing.value = true;
    notice.warn("未找到对应的结构化需求，只能按用例自身的追溯信息查看来源。");
  }
}

onMounted(load);
</script>

<template>
  <div class="stack">
    <PageHead
      :title="data?.doc_title || '用例集'"
      :note="data ? `${data.suite_id} · 生成于 ${formatDateTime(data.created_at)} · 方法 ${data.methods.map(methodLabel).join(' / ')}` : '正在载入…'"
      back-to="/suites"
      back-label="用例集"
    >
      <template #actions>
        <el-button :disabled="!data" title="重新载入用例集与需求追溯" @click="load">刷新</el-button>
        <el-button
          v-if="data?.doc_id"
          title="打开该用例集对应的结构化需求"
          @click="router.push(`/documents/${data.doc_id}/requirement`)"
        >
          查看结构化需求
        </el-button>
        <el-button
          type="primary"
          :icon="Download"
          :disabled="!data"
          :loading="exporting === 'excel'"
          title="导出为 Excel：用例明细 / 统计 / 需求追溯"
          @click="exportAs('excel')"
        >
          导出 Excel
        </el-button>
        <el-button
          :disabled="!data"
          :loading="exporting === 'json'"
          title="导出为 JSON，便于二次处理"
          @click="exportAs('json')"
        >
          JSON
        </el-button>
      </template>
    </PageHead>

    <ErrorNote :error="suite.error.value" />

    <el-skeleton v-if="suite.loading.value && !data" :rows="6" animated class="pad" />

    <EmptyState
      v-else-if="!data"
      title="找不到这份用例集"
      hint="它可能已被清理。回到用例集列表选择其它记录，或重新生成一份。"
    >
      <el-button type="primary" @click="router.push('/suites')">返回用例集列表</el-button>
    </EmptyState>

    <template v-else>
      <StatStrip :items="statItems" />

      <div v-if="data.generation_meta.warnings?.length" class="warns">
        <p class="warns__title">生成过程有 {{ data.generation_meta.warnings.length }} 条提示</p>
        <ul>
          <li
            v-for="(warning, index) in data.generation_meta.warnings.slice(0, 8)"
            :key="index"
          >
            {{ warning }}
          </li>
        </ul>
      </div>

      <section class="card">
        <div class="card__head">
          <span class="card__title">需求追溯</span>
          <span class="dim trace__note">
            {{ requirement ? "每条需求的用例覆盖量与来源用例" : "未载入结构化需求" }}
          </span>
        </div>

        <div v-if="!requirement" class="card__body">
          <p class="dim">
            {{
              requirementMissing
                ? "这份用例集对应的结构化需求已不在存储中，只能按用例自身的「追溯」字段查看来源。"
                : "正在载入结构化需求…"
            }}
          </p>
        </div>

        <ul v-else class="trace">
          <li
            v-for="row in coverage"
            :key="row.item.id"
            class="trace__row"
            :class="{ 'trace__row--gap': row.count === 0 }"
          >
            <div class="trace__head">
              <span class="stamp">{{ row.item.id }}</span>
              <span class="trace__title">{{ row.item.title }}</span>
              <PriorityMark :value="row.item.priority" />
              <span class="spacer"></span>
              <span class="num trace__count">{{ row.count }} 条</span>
            </div>

            <div class="extent" :aria-label="`覆盖 ${row.count} 条用例`">
              <span
                class="extent__fill"
                :style="{ '--extent': row.count === 0 ? 0 : row.count / maxCoverage }"
                :class="{ 'extent__fill--gap': row.count === 0 }"
              ></span>
            </div>

            <div v-if="row.cases.length" class="seealso">
              <button
                v-for="testCase in row.cases.slice(0, 10)"
                :key="testCase.case_id"
                type="button"
                class="sibling"
                :title="testCase.title"
                @click="focusedCase = testCase.case_id"
              >
                <span class="mono">{{ testCase.case_id }}</span>
              </button>
              <span v-if="row.cases.length > 10" class="dim seealso__more">
                另 {{ row.cases.length - 10 }} 条
              </span>
            </div>
            <p v-else class="dim trace__gap">
              这条需求没有生成任何用例。常见原因是文档里缺少字段约束或流程描述，可以补充后重新解析。
            </p>
          </li>
        </ul>

        <div v-if="uncovered.length" class="card__foot">
          未覆盖 {{ uncovered.length }} 条需求：
          <span class="mono">{{ uncovered.map((row) => row.item.id).join("、") }}</span>
        </div>
      </section>

      <CaseTable
        :cases="data.cases"
        :items="itemsIndex"
        :doc-id="data.doc_id"
        :focus-case-id="focusedCase"
      />
    </template>
  </div>
</template>

<style scoped>
.pad {
  padding: var(--s5);
}

.warns {
  padding: var(--s3) var(--s4);
  background: var(--warn-wash);
  border: 1px solid rgba(138, 97, 20, 0.3);
  border-radius: var(--radius);
}

.warns__title {
  font-size: var(--fs-sm);
  font-weight: 500;
  color: var(--warn);
}

.warns ul {
  margin: var(--s2) 0 0;
  padding-left: var(--s5);
  font-size: var(--fs-xs);
  line-height: 1.6;
  color: var(--ink-2);
}

.trace__note {
  font-size: var(--fs-xs);
}

.trace {
  margin: 0;
  padding: 0;
  list-style: none;
}

.trace__row {
  padding: var(--s3) var(--s4);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.trace__row + .trace__row {
  border-top: 1px solid var(--rule);
}

.trace__head {
  display: flex;
  align-items: center;
  gap: var(--s2);
  flex-wrap: wrap;
}

.trace__title {
  font-size: var(--fs-base);
  color: var(--ink);
}

.trace__count {
  font-size: var(--fs-xs);
  color: var(--ink-2);
}

.extent {
  height: 3px;
  background: var(--paper-sunk);
  border-radius: 999px;
  overflow: hidden;
}

.extent__fill {
  display: block;
  width: 100%;
  height: 100%;
  background: var(--stamp);
  transform-origin: left center;
  transform: scaleX(var(--extent, 0));
  transition: transform var(--dur) var(--ease);
}

.extent__fill--gap {
  background: transparent;
}

.trace__row--gap {
  background: var(--warn-wash);
}

.trace__gap {
  font-size: var(--fs-xs);
  line-height: 1.55;
}

.seealso__more {
  font-size: var(--fs-xs);
}

.sibling {
  appearance: none;
  border: 1px solid var(--rule-strong);
  background: var(--card);
  border-radius: var(--radius-sm);
  padding: 0 6px;
  font: inherit;
  font-size: var(--fs-xs);
  color: var(--ink-2);
  cursor: pointer;
  transition: border-color var(--dur-fast) var(--ease), background-color var(--dur-fast) var(--ease);
}

.sibling:hover {
  border-color: var(--stamp);
  background: var(--stamp-wash);
  color: var(--stamp-deep);
}

.card__foot {
  padding: var(--s3) var(--s4);
  border-top: 1px solid var(--rule);
  background: var(--paper-sunk);
  font-size: var(--fs-xs);
  color: var(--ink-2);
}
</style>
