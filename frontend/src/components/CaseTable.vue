<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { RefreshLeft, Search } from "@element-plus/icons-vue";

import type { RequirementItem, TestCase } from "@/api";
import { CASE_TYPES, PRIORITY_ORDER, priorityRank } from "@/utils/labels";
import EmptyState from "./EmptyState.vue";
import MethodTag from "./MethodTag.vue";
import PriorityMark from "./PriorityMark.vue";
import TraceCard from "./TraceCard.vue";

type SortKey = "case_id" | "module" | "priority" | "method" | "type";

const props = withDefaults(
  defineProps<{
    cases: TestCase[];
    items?: Map<string, RequirementItem>;
    loading?: boolean;
    docId?: string;
    pageSize?: number;
    focusCaseId?: string | null;
  }>(),
  { pageSize: 20 },
);

const keyword = ref("");
const methodFilter = ref("");
const typeFilter = ref("");
const priorityFilter = ref("");
const sortKey = ref<SortKey>("case_id");
const sortOrder = ref<"asc" | "desc">("asc");
const page = ref(1);
const size = ref(props.pageSize);
const expanded = ref<string[]>([]);

const methodOptions = computed(() => {
  const present = new Set<string>();
  props.cases.forEach((item) => {
    if (item.design_method) present.add(item.design_method);
  });
  const ordered = ["equivalence", "boundary", "scenario"].filter((m) => present.has(m));
  const extra = [...present].filter((m) => !ordered.includes(m)).sort();
  return [...ordered, ...extra];
});

const typeOptions = computed(() => {
  const present = new Set(props.cases.map((item) => item.case_type));
  const ordered = CASE_TYPES.filter((t) => present.has(t));
  const extra = [...present].filter((t) => !CASE_TYPES.includes(t)).sort();
  return [...ordered, ...extra];
});

const hasFilters = computed(
  () =>
    keyword.value.trim() !== "" ||
    methodFilter.value !== "" ||
    typeFilter.value !== "" ||
    priorityFilter.value !== "",
);

const filtered = computed(() => {
  const needle = keyword.value.trim().toLowerCase();
  return props.cases.filter((item) => {
    if (methodFilter.value && item.design_method !== methodFilter.value) return false;
    if (typeFilter.value && item.case_type !== typeFilter.value) return false;
    if (priorityFilter.value && item.priority !== priorityFilter.value) return false;
    if (!needle) return true;
    const haystack = [
      item.case_id,
      item.title,
      item.module,
      item.expected_result,
      ...Object.keys(item.test_data ?? {}),
      ...Object.values(item.test_data ?? {}),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(needle);
  });
});

const sorted = computed(() => {
  const list = [...filtered.value];
  const direction = sortOrder.value === "asc" ? 1 : -1;
  list.sort((a, b) => {
    let delta = 0;
    switch (sortKey.value) {
      case "priority":
        delta = priorityRank(a.priority) - priorityRank(b.priority);
        break;
      case "module":
        delta = a.module.localeCompare(b.module, "zh-Hans-CN");
        break;
      case "method":
        delta = a.design_method.localeCompare(b.design_method);
        break;
      case "type":
        delta = a.case_type.localeCompare(b.case_type, "zh-Hans-CN");
        break;
      default:
        delta = a.case_id.localeCompare(b.case_id);
    }
    if (delta === 0) delta = a.case_id.localeCompare(b.case_id);
    return delta * direction;
  });
  return list;
});

const paged = computed(() =>
  sorted.value.slice((page.value - 1) * size.value, page.value * size.value),
);

const siblingsIndex = computed(() => {
  const index = new Map<string, TestCase[]>();
  props.cases.forEach((item) => {
    item.requirement_ids.forEach((reqId) => {
      const bucket = index.get(reqId) ?? [];
      bucket.push(item);
      index.set(reqId, bucket);
    });
  });
  return index;
});

function siblingsOf(item: TestCase): TestCase[] {
  const ids = new Set(item.requirement_ids);
  const seen = new Map<string, TestCase>();
  ids.forEach((reqId) => {
    (siblingsIndex.value.get(reqId) ?? []).forEach((candidate) => {
      if (candidate.case_id !== item.case_id) seen.set(candidate.case_id, candidate);
    });
  });
  return [...seen.values()].slice(0, 6);
}

function onSortChange(payload: { prop: string | null; order: string | null }): void {
  if (!payload.prop || !payload.order) {
    sortKey.value = "case_id";
    sortOrder.value = "asc";
    return;
  }
  sortKey.value = payload.prop as SortKey;
  sortOrder.value = payload.order === "descending" ? "desc" : "asc";
}

function onExpandChange(row: TestCase, rows: TestCase[]): void {
  expanded.value = rows.map((item) => item.case_id);
  if (row && expanded.value.includes(row.case_id) === false) {
    expanded.value = expanded.value.filter((id) => id !== row.case_id);
  }
}

function focusCase(caseId: string): void {
  const position = sorted.value.findIndex((item) => item.case_id === caseId);
  if (position < 0) return;
  page.value = Math.floor(position / size.value) + 1;
  expanded.value = [caseId];
}

function resetFilters(): void {
  keyword.value = "";
  methodFilter.value = "";
  typeFilter.value = "";
  priorityFilter.value = "";
}

watch([keyword, methodFilter, typeFilter, priorityFilter], () => {
  page.value = 1;
});

watch(
  () => props.cases,
  () => {
    page.value = 1;
    expanded.value = [];
  },
);

watch(
  () => props.focusCaseId,
  (caseId) => {
    if (caseId) focusCase(caseId);
  },
);
</script>

<template>
  <section class="cases card">
    <div class="cases__toolbar">
      <el-input
        v-model="keyword"
        class="cases__search"
        placeholder="搜索编号、标题、模块、预期结果或测试数据"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select v-model="methodFilter" placeholder="设计方法" clearable class="cases__select">
        <el-option v-for="method in methodOptions" :key="method" :label="method" :value="method" />
      </el-select>

      <el-select v-model="typeFilter" placeholder="用例类型" clearable class="cases__select">
        <el-option v-for="type in typeOptions" :key="type" :label="type" :value="type" />
      </el-select>

      <el-select v-model="priorityFilter" placeholder="优先级" clearable class="cases__select cases__select--narrow">
        <el-option v-for="level in PRIORITY_ORDER" :key="level" :label="level" :value="level" />
      </el-select>

      <el-button v-if="hasFilters" :icon="RefreshLeft" text @click="resetFilters">
        清除筛选
      </el-button>

      <span class="spacer"></span>

      <p class="cases__count num">
        <template v-if="hasFilters">筛选后 {{ sorted.length }} / </template>
        共 {{ cases.length }} 条
      </p>
    </div>

    <el-skeleton v-if="loading" :rows="6" animated class="cases__skeleton" />

    <EmptyState
      v-else-if="!cases.length"
      title="这个用例集还没有内容"
      hint="回到工作台粘贴需求文本或上传文档，选择设计方法后生成用例。"
    >
      <slot name="empty-actions" />
    </EmptyState>

    <EmptyState
      v-else-if="!sorted.length"
      title="当前筛选下没有匹配的用例"
      hint="试着放宽关键词，或清除方法 / 类型 / 优先级的限制。"
    >
      <el-button @click="resetFilters">清除筛选</el-button>
    </EmptyState>

    <template v-else>
      <el-table
        :data="paged"
        row-key="case_id"
        :expand-row-keys="expanded"
        scrollbar-always-on
        class="cases__table"
        @sort-change="onSortChange"
        @expand-change="onExpandChange"
      >
        <el-table-column type="expand" width="38">
          <template #default="{ row }">
            <TraceCard
              :case-item="row"
              :items="items"
              :doc-id="docId"
              :siblings="siblingsOf(row)"
              @focus-case="focusCase"
            />
          </template>
        </el-table-column>

        <el-table-column prop="case_id" label="用例编号" width="112" sortable="custom">
          <template #default="{ row }">
            <span class="mono cases__id">{{ row.case_id }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="module" label="模块" width="96" sortable="custom" show-overflow-tooltip />

        <el-table-column prop="title" label="标题" min-width="230">
          <template #default="{ row }">
            <span class="cases__title clamp-2" :title="row.title">{{ row.title }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="method" label="方法" width="96" sortable="custom">
          <template #default="{ row }">
            <MethodTag :value="row.design_method" />
          </template>
        </el-table-column>

        <el-table-column prop="type" label="类型" width="60" sortable="custom" />

        <el-table-column prop="priority" label="优先级" width="84" sortable="custom">
          <template #default="{ row }">
            <PriorityMark :value="row.priority" />
          </template>
        </el-table-column>

        <el-table-column label="测试数据" width="146">
          <template #default="{ row }">
            <span class="cases__data pre clamp-3" :title="Object.entries(row.test_data || {}).map(([k, v]) => `${k} = ${v === '' ? '(空)' : v}`).join('\n')">{{ Object.entries(row.test_data || {}).map(([k, v]) => `${k} = ${v === '' ? '(空)' : v}`).join('\n') || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="预期结果" min-width="230">
          <template #default="{ row }">
            <span class="cases__expected pre clamp-3" :title="row.expected_result">{{ row.expected_result || '—' }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="cases__foot">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="sorted.length"
          :page-sizes="[20, 50, 100, 200]"
          layout="total, sizes, prev, pager, next, jumper"
          background
        />
        <p class="cases__hint dim">展开任意一行，可抽出一张追溯卡。</p>
      </div>
    </template>
  </section>
</template>

<style scoped>
.cases__toolbar {
  display: flex;
  align-items: center;
  gap: var(--s2);
  flex-wrap: wrap;
  padding: var(--s3) var(--s4);
  border-bottom: 1px solid var(--rule);
}

.cases__search {
  width: min(340px, 46vw);
}

.cases__select {
  width: 148px;
}

.cases__select--narrow {
  width: 108px;
}

.cases__count {
  font-size: var(--fs-xs);
  color: var(--ink-3);
}

.cases__table {
  border-radius: 0;
}

.cases__id {
  font-size: var(--fs-xs);
  color: var(--ink);
  font-weight: 500;
  white-space: nowrap;
}

.cases__title {
  display: block;
  font-size: var(--fs-table);
  line-height: 1.5;
  color: var(--ink);
}

.cases__data,
.cases__expected {
  font-size: var(--fs-xs);
  color: var(--ink-3);
}

.cases__expected {
  color: var(--ink-2);
}

.clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  white-space: pre-wrap;
  word-break: break-word;
}

.cases__skeleton {
  padding: var(--s5);
}

.cases__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s4);
  flex-wrap: wrap;
  padding: var(--s3) var(--s4);
  border-top: 1px solid var(--rule);
}

.cases__hint {
  font-size: var(--fs-xs);
}

@media (max-width: 900px) {
  .cases__search {
    width: 100%;
  }

  .cases__select {
    flex: 1 1 120px;
    width: auto;
  }

  .cases__select--narrow {
    flex: 0 1 100px;
  }
}
</style>
