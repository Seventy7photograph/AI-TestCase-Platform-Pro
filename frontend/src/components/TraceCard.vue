<script setup lang="ts">
import { computed } from "vue";

import type { RequirementItem, TestCase } from "@/api";
import { notice } from "@/composables/useNotice";
import { caseToPlainText, methodLabel } from "@/utils/labels";

const props = defineProps<{
  caseItem: TestCase;
  items?: Map<string, RequirementItem>;
  siblings: TestCase[];
  docId?: string;
}>();

const emit = defineEmits<{ (event: "focus-case", caseId: string): void }>();

const requirements = computed(() => {
  const index = props.items;
  return props.caseItem.requirement_ids.map((id) => ({
    id,
    item: index?.get(id) ?? null,
  }));
});

const coveredMethods = computed(() => {
  const list = props.caseItem.covered_methods?.length
    ? props.caseItem.covered_methods
    : [props.caseItem.design_method];
  return list.map((method) => methodLabel(method)).join(" · ");
});

const dataRows = computed(() =>
  Object.entries(props.caseItem.test_data ?? {}).map(([key, value]) => ({
    key,
    value: value === "" ? "(空)" : value,
  })),
);

async function copyCase(): Promise<void> {
  try {
    await navigator.clipboard.writeText(caseToPlainText(props.caseItem));
    notice.success("已复制用例文本，可直接粘贴到禅道 / Jira");
  } catch {
    notice.error("浏览器拒绝了剪贴板访问，请手动选中复制。");
  }
}
</script>

<template>
  <article class="trace-card">
    <div class="trace-card__top">
      <div class="seealso">
        <span class="label">追溯</span>
        <template v-for="entry in requirements" :key="entry.id">
          <RouterLink
            v-if="docId"
            class="stamp"
            :to="{ name: 'requirement', params: { docId } }"
            :title="entry.item?.title || entry.id"
          >
            {{ entry.id }}
          </RouterLink>
          <span v-else class="stamp" :title="entry.item?.title || entry.id">
            {{ entry.id }}
          </span>
        </template>
        <span class="trace-card__methods">{{ coveredMethods }}</span>
      </div>
      <button
        type="button"
        class="trace-card__copy"
        title="复制为纯文本，便于粘贴到测试管理平台"
        @click="copyCase"
      >
        复制用例
      </button>
    </div>

    <hr class="trace-card__rule" />

    <div class="trace-card__grid">
      <div class="trace-card__col">
        <section v-if="requirements.length" class="block">
          <p class="label">来源需求</p>
          <ul class="reqs">
            <li v-for="entry in requirements" :key="entry.id">
              <span class="reqs__id mono">{{ entry.id }}</span>
              <span class="reqs__title">{{ entry.item?.title || "未载入需求条目" }}</span>
            </li>
          </ul>
          <pre
            v-for="entry in requirements"
            :key="`raw-${entry.id}`"
            class="reqs__raw pre"
            :title="entry.item?.raw_text || ''"
          >{{ entry.item?.raw_text || entry.item?.description || "（无原文片段）" }}</pre>
        </section>

        <section class="block">
          <p class="label">执行步骤</p>
          <ol class="steps">
            <li v-for="step in caseItem.steps" :key="step.no">
              <span class="steps__no num">{{ step.no }}</span>
              <span class="steps__body">
                <span class="steps__action">{{ step.action }}</span>
                <span v-if="step.expected" class="steps__expected">→ 预期：{{ step.expected }}</span>
              </span>
            </li>
          </ol>
          <p v-if="!caseItem.steps.length" class="dim">该用例未拆解步骤。</p>
        </section>

        <section class="block">
          <p class="label">预期结果</p>
          <p class="pre">{{ caseItem.expected_result || "—" }}</p>
        </section>
      </div>

      <div class="trace-card__col">
        <section class="block">
          <p class="label">测试数据</p>
          <table v-if="dataRows.length" class="data">
            <tbody>
              <tr v-for="row in dataRows" :key="row.key">
                <th scope="row" class="mono">{{ row.key }}</th>
                <td class="pre">{{ row.value }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else class="dim">无字段级数据。</p>
        </section>

        <section v-if="caseItem.preconditions.length" class="block">
          <p class="label">前置条件</p>
          <ul class="plain">
            <li v-for="(item, index) in caseItem.preconditions" :key="index">{{ item }}</li>
          </ul>
        </section>

        <section class="block">
          <p class="label">交叉索引 · 同源用例</p>
          <div v-if="siblings.length" class="seealso">
            <button
              v-for="sibling in siblings"
              :key="sibling.case_id"
              type="button"
              class="sibling"
              :title="sibling.title"
              @click="emit('focus-case', sibling.case_id)"
            >
              <span class="mono">{{ sibling.case_id }}</span>
              <span class="sibling__title">{{ sibling.title }}</span>
            </button>
          </div>
          <p v-else class="dim">无其它用例覆盖同一需求条目。</p>
        </section>

        <section v-if="caseItem.remarks" class="block">
          <p class="label">备注</p>
          <p class="pre dim">{{ caseItem.remarks }}</p>
        </section>
      </div>
    </div>
  </article>
</template>

<style scoped>
.trace-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--s3);
  flex-wrap: wrap;
}

.trace-card__methods {
  font-size: var(--fs-xs);
  color: var(--ink-3);
}

.trace-card__copy {
  appearance: none;
  border: 1px solid var(--rule-strong);
  background: var(--card);
  border-radius: var(--radius-sm);
  padding: 2px 8px;
  font: inherit;
  font-size: var(--fs-xs);
  color: var(--ink-2);
  cursor: pointer;
  transition: background-color var(--dur-fast) var(--ease);
}

.trace-card__copy:hover {
  background: var(--paper-sunk);
  color: var(--ink);
}

.trace-card__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr);
  gap: var(--s5);
}

@media (max-width: 1100px) {
  .trace-card__grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

.trace-card__col {
  display: flex;
  flex-direction: column;
  gap: var(--s4);
  min-width: 0;
}

.block {
  min-width: 0;
}

.block .label {
  display: block;
  margin-bottom: 5px;
}

.reqs {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.reqs li {
  display: flex;
  gap: var(--s2);
  align-items: baseline;
}

.reqs__id {
  font-size: var(--fs-xs);
  color: var(--stamp-deep);
  font-weight: 500;
  flex: none;
}

.reqs__title {
  font-size: var(--fs-sm);
  color: var(--ink);
}

.reqs__raw {
  margin: var(--s2) 0 0;
  padding: var(--s2) var(--s3);
  max-height: 116px;
  overflow: auto;
  font-family: var(--font-ui);
  font-size: var(--fs-xs);
  line-height: 1.6;
  color: var(--ink-3);
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: var(--radius-sm);
}

.steps {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--s2);
}

.steps li {
  display: flex;
  gap: var(--s3);
  align-items: baseline;
}

.steps__no {
  flex: none;
  width: 18px;
  font-size: var(--fs-xs);
  color: var(--ink-4);
}

.steps__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.steps__action {
  font-size: var(--fs-sm);
  color: var(--ink);
}

.steps__expected {
  font-size: var(--fs-xs);
  color: var(--ink-3);
}

.data {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-xs);
}

.data th,
.data td {
  border-bottom: 1px solid var(--rule);
  padding: 5px 8px;
  text-align: left;
  vertical-align: top;
}

.data th {
  width: 34%;
  font-weight: 500;
  color: var(--ink-3);
}

.data td {
  color: var(--ink);
}

.plain {
  margin: 0;
  padding-left: 16px;
  font-size: var(--fs-sm);
  color: var(--ink-2);
}

.sibling {
  appearance: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  border: 1px solid var(--rule-strong);
  background: var(--card);
  border-radius: var(--radius-sm);
  padding: 1px 7px;
  font: inherit;
  font-size: var(--fs-xs);
  color: var(--ink-2);
  cursor: pointer;
  transition: border-color var(--dur-fast) var(--ease),
    background-color var(--dur-fast) var(--ease);
}

.sibling:hover {
  border-color: var(--stamp);
  background: var(--stamp-wash);
  color: var(--stamp-deep);
}

.sibling__title {
  max-width: 22ch;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
