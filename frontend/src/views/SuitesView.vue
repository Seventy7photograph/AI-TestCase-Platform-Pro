<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";

import { api } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { notice } from "@/composables/useNotice";
import { METHOD_SHORT, formatDateTime, methodLabel } from "@/utils/labels";
import EmptyState from "@/components/EmptyState.vue";
import ErrorNote from "@/components/ErrorNote.vue";
import PageHead from "@/components/PageHead.vue";

const router = useRouter();
const suites = useAsync(() => api.suites(30));

const rows = computed(() => suites.data.value ?? []);

onMounted(() => {
  void suites.run();
});

async function refresh(): Promise<void> {
  const list = await suites.run();
  if (list) {
    notice.success(`已刷新，共 ${list.length} 份用例集。`);
  } else if (suites.error.value) {
    notice.error(suites.error.value);
  }
}
</script>

<template>
  <div class="stack">
    <PageHead
      title="用例集"
      note="服务端保存的最近 30 次生成结果。打开任意一份可以筛选、追溯来源需求，并导出 Excel 或 JSON。"
    >
      <template #actions>
        <el-button title="重新载入最近生成的用例集列表" @click="refresh">刷新</el-button>
        <el-button type="primary" @click="router.push('/')">去生成</el-button>
      </template>
    </PageHead>

    <ErrorNote :error="suites.error.value" />

    <el-skeleton v-if="suites.loading.value && !rows.length" :rows="6" animated class="pad" />

    <EmptyState
      v-else-if="!rows.length"
      title="还没有生成过用例集"
      hint="在工作台粘贴需求文本或上传文档，生成第一份用例集后就会出现在这里。"
    >
      <el-button type="primary" @click="router.push('/')">去工作台生成</el-button>
    </EmptyState>

    <ul v-else class="index">
      <li v-for="suite in rows" :key="suite.suite_id" class="index__row">
        <button type="button" class="index__main" @click="router.push(`/suites/${suite.suite_id}`)">
          <span class="index__head">
            <span class="stamp stamp--quiet">{{ suite.suite_id }}</span>
            <span class="index__title">{{ suite.doc_title || "未命名文档" }}</span>
          </span>
          <span class="index__meta mono">
            {{ formatDateTime(suite.created_at) }} ·
            {{ suite.cases.length }} 条用例 ·
            去重 {{ suite.stats.duplicate_removed }} ·
            覆盖 {{ Object.keys(suite.stats.requirement_coverage || {}).length }} 条需求
          </span>
          <span class="index__methods">
            <span
              v-for="method in suite.methods"
              :key="method"
              class="chip mono"
              :title="methodLabel(method)"
            >
              {{ METHOD_SHORT[method] || method }}
            </span>
            <span
              v-if="suite.generation_meta.llm_used"
              class="chip chip--accent mono"
              title="生成阶段调用了大模型增强"
            >
              LLM
            </span>
            <span v-else class="chip mono" title="由规则引擎生成，未调用大模型">规则</span>
          </span>
        </button>
        <div class="index__actions">
          <el-button
            text
            title="打开用例集：筛选、追溯来源需求并导出"
            @click="router.push(`/suites/${suite.suite_id}`)"
          >
            打开
          </el-button>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.pad {
  padding: var(--s5);
}

.index {
  margin: 0;
  padding: 0;
  list-style: none;
  background: var(--card);
  border: 1px solid var(--card-edge);
  border-radius: var(--radius);
  overflow: hidden;
}

.index__row {
  display: flex;
  align-items: center;
  gap: var(--s4);
  padding: var(--s3) var(--s4);
}

.index__row + .index__row {
  border-top: 1px solid var(--rule);
}

.index__main {
  appearance: none;
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-start;
  border: 0;
  background: transparent;
  padding: 0;
  font: inherit;
  text-align: left;
  cursor: pointer;
  color: inherit;
}

.index__head {
  display: flex;
  align-items: center;
  gap: var(--s2);
  min-width: 0;
}

.index__title {
  font-size: var(--fs-base);
  font-weight: 500;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.index__meta {
  font-size: var(--fs-xs);
  color: var(--ink-3);
}

.index__methods {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.chip {
  font-size: 10px;
  letter-spacing: 0.03em;
  color: var(--ink-3);
  border: 1px solid var(--rule-strong);
  border-radius: var(--radius-sm);
  padding: 0 4px;
}

.chip--accent {
  color: var(--stamp-deep);
  border-color: rgba(26, 127, 169, 0.38);
  background: var(--stamp-wash);
}

.index__actions {
  flex: none;
}

.index__main:hover .index__title {
  color: var(--stamp-deep);
}
</style>
