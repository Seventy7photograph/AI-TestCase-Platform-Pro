<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import { api } from "@/api";
import type { DocumentSummary } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatBytes, formatDateTime } from "@/utils/labels";
import EmptyState from "@/components/EmptyState.vue";
import ErrorNote from "@/components/ErrorNote.vue";
import PageHead from "@/components/PageHead.vue";

const router = useRouter();
const documents = useAsync(() => api.documents(50));
const parsing = ref<string>("");
const useLlm = ref(true);
const maxItems = ref(8);
const previewOf = ref<DocumentSummary | null>(null);

const rows = computed(() => documents.data.value ?? []);

onMounted(() => {
  void documents.run();
});

async function parseRequirement(row: DocumentSummary): Promise<void> {
  parsing.value = row.doc_id;
  try {
    await api.parseRequirement({
      doc_id: row.doc_id,
      title: row.filename.replace(/\.[^.]+$/, ""),
      use_llm: useLlm.value,
      max_items: maxItems.value,
    });
    ElMessage.success(`已解析 ${row.filename}`);
    await router.push(`/documents/${row.doc_id}/requirement`);
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "解析失败");
  } finally {
    parsing.value = "";
  }
}
</script>

<template>
  <div class="stack">
    <PageHead
      title="文档与需求"
      note="服务端保存的最近 50 份上传文档。解析成结构化需求后，才能看到字段约束、业务流程与异常场景。"
    >
      <template #actions>
        <el-button @click="documents.run()">刷新</el-button>
        <el-button type="primary" @click="router.push('/')">上传新文档</el-button>
      </template>
    </PageHead>

    <ErrorNote :error="documents.error.value" />

    <section class="card">
      <div class="card__head">
        <span class="card__title">解析设置</span>
        <span class="dim doc__note">对下方任意文档生效</span>
      </div>
      <div class="card__body row row--wrap">
        <label class="inline">
          <el-switch v-model="useLlm" />
          <span>使用大模型辅助解析</span>
        </label>
        <label class="inline">
          <span class="label">最多解析条目</span>
          <el-input-number v-model="maxItems" :min="1" :max="50" size="small" controls-position="right" />
        </label>
        <span class="dim doc__note">
          未配置 Key 时解析会自动降级为规则引擎，结果里会标注口径。
        </span>
      </div>
    </section>

    <el-skeleton v-if="documents.loading.value && !rows.length" :rows="6" animated class="pad" />

    <EmptyState
      v-else-if="!rows.length"
      title="还没有上传过文档"
      hint="在工作台选择「上传文档」，支持 docx / pdf / txt / md / csv / json。"
    >
      <el-button type="primary" @click="router.push('/')">去工作台</el-button>
    </EmptyState>

    <section v-else class="card">
      <el-table :data="rows" row-key="doc_id">
        <el-table-column label="文件名" min-width="240">
          <template #default="{ row }">
            <span class="doc__name">{{ row.filename }}</span>
            <span class="doc__id mono">{{ row.doc_id }}</span>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="76">
          <template #default="{ row }">
            <span class="mono doc__ext">{{ row.extension || "—" }}</span>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="92">
          <template #default="{ row }">
            <span class="num">{{ formatBytes(row.size_bytes) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="字数" width="92">
          <template #default="{ row }">
            <span class="num">{{ row.char_count }}</span>
          </template>
        </el-table-column>
        <el-table-column label="解析器" width="104" prop="parser" />
        <el-table-column label="上传时间" width="150">
          <template #default="{ row }">
            <span class="num">{{ formatDateTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="提示" width="76">
          <template #default="{ row }">
            <span v-if="row.warnings.length" class="num doc__warn">{{ row.warnings.length }}</span>
            <span v-else class="dim">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button text @click="previewOf = row">预览</el-button>
            <el-button
              text
              type="primary"
              :loading="parsing === row.doc_id"
              @click="parseRequirement(row)"
            >
              解析需求
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-drawer v-model="previewOf" :title="previewOf?.filename || '文档预览'" size="520px">
      <div v-if="previewOf" class="stack stack--tight">
        <dl class="meta">
          <div><dt class="label">文档 ID</dt><dd class="mono">{{ previewOf.doc_id }}</dd></div>
          <div><dt class="label">解析器</dt><dd>{{ previewOf.parser }}</dd></div>
          <div><dt class="label">字数</dt><dd class="num">{{ previewOf.char_count }}</dd></div>
          <div><dt class="label">行数</dt><dd class="num">{{ previewOf.line_count }}</dd></div>
          <div v-if="previewOf.table_count">
            <dt class="label">表格</dt><dd class="num">{{ previewOf.table_count }}</dd>
          </div>
          <div v-if="previewOf.page_count">
            <dt class="label">页数</dt><dd class="num">{{ previewOf.page_count }}</dd>
          </div>
        </dl>

        <div v-if="previewOf.warnings.length" class="warns">
          <p
            v-for="(warning, index) in previewOf.warnings"
            :key="index"
            class="warns__line"
          >
            {{ warning }}
          </p>
        </div>

        <p class="label">正文摘录</p>
        <pre class="preview pre">{{ previewOf.preview || "（无正文）" }}</pre>

        <el-button type="primary" @click="previewOf && parseRequirement(previewOf)">
          解析成结构化需求
        </el-button>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.pad {
  padding: var(--s5);
}

.doc__note {
  font-size: var(--fs-xs);
}

.inline {
  display: inline-flex;
  align-items: center;
  gap: var(--s2);
  font-size: var(--fs-base);
  color: var(--ink-2);
  cursor: pointer;
}

.doc__name {
  display: block;
  font-size: var(--fs-base);
  color: var(--ink);
}

.doc__id {
  display: block;
  font-size: var(--fs-xs);
  color: var(--ink-4);
}

.doc__ext {
  font-size: var(--fs-xs);
  color: var(--ink-2);
}

.doc__warn {
  color: var(--warn);
}

.meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--s3);
  margin: 0;
}

.meta dd {
  margin: 2px 0 0;
  font-size: var(--fs-base);
  color: var(--ink);
}

.warns {
  padding: var(--s2) var(--s3);
  background: var(--warn-wash);
  border: 1px solid rgba(138, 97, 20, 0.3);
  border-radius: var(--radius);
}

.warns__line {
  font-size: var(--fs-xs);
  line-height: 1.55;
  color: var(--ink-2);
}

.preview {
  margin: 0;
  padding: var(--s3);
  max-height: 420px;
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
