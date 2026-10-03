<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import type { UploadFile } from "element-plus";
import { ElMessage } from "element-plus";
import { Download, Document as DocumentIcon, UploadFilled } from "@element-plus/icons-vue";

import { api, saveBlob } from "@/api";
import type { DocumentSummary, GenerateResult, RequirementItem } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { RESERVED_METHODS, V1_METHODS, formatBytes, formatDuration, methodLabel } from "@/utils/labels";
import CaseTable from "@/components/CaseTable.vue";
import ErrorNote from "@/components/ErrorNote.vue";
import PageHead from "@/components/PageHead.vue";
import StatStrip from "@/components/StatStrip.vue";
import type { StatItem } from "@/components/StatStrip.vue";

const router = useRouter();

const mode = ref<"text" | "upload">("text");
const text = ref("");
const title = ref("粘贴的需求文本");
const docId = ref<string | null>(null);
const docInfo = ref<DocumentSummary | null>(null);
const uploading = ref(false);

const methods = ref<string[]>([...V1_METHODS]);
const maxItems = ref(8);
const useLlm = ref(true);
const useLlmInDesign = ref(false);

const generate = useAsync(api.generate);
const exportExcel = useAsync(() => download("excel"));
const exportJson = useAsync(() => download("json"));

const result = computed<GenerateResult | null>(() => generate.data.value);

const itemsIndex = computed(() => {
  const map = new Map<string, RequirementItem>();
  result.value?.requirement_doc.items.forEach((item) => map.set(item.id, item));
  return map;
});

const canGenerate = computed(() => {
  if (!methods.value.length) return false;
  if (mode.value === "upload") return docId.value !== null;
  return text.value.trim().length > 0;
});

const methodError = computed(() => (methods.value.length ? "" : "请至少选择一种设计方法。"));

const statItems = computed<StatItem[]>(() => {
  const current = result.value;
  if (!current) return [];
  const { suite, requirement_doc } = current;
  const stats = suite.stats;
  const covered = Object.keys(stats.requirement_coverage ?? {}).length;
  const items = requirement_doc.items.length;
  const parse = requirement_doc.parse_meta;
  const generation = suite.generation_meta;
  return [
    { label: "用例总数", value: stats.total, hint: "去重合并后的最终条数" },
    {
      label: "去重剔除",
      value: stats.duplicate_removed,
      hint: "精确指纹与跨方法语义重叠合并掉的重复用例",
    },
    {
      label: "需求覆盖",
      value: `${covered} / ${items}`,
      tone: covered >= items && items > 0 ? "good" : "warn",
      hint: "至少生成 1 条用例的需求条目数 / 解析出的条目总数",
    },
    {
      label: "解析口径",
      value: parse.llm_used ? `LLM · ${parse.provider}` : "规则引擎",
      tone: parse.fallback_used ? "warn" : "default",
      hint: parse.fallback_used
        ? `已降级为规则解析：${parse.fallback_reason || "未配置或调用失败"}`
        : "需求文本 → 结构化需求模型所使用的引擎",
    },
    {
      label: "生成口径",
      value: generation.llm_used ? "LLM 增强" : "规则引擎",
      hint: "由「生成阶段也调用大模型」开关控制",
    },
    { label: "解析耗时", value: formatDuration(parse.elapsed_ms), hint: "需求解析阶段耗时" },
  ];
});

function toggleMode(next: "text" | "upload"): void {
  mode.value = next;
}

async function onFileChange(file: UploadFile): Promise<void> {
  const raw = file.raw;
  if (!raw) return;
  if (raw.size > 20 * 1024 * 1024) {
    ElMessage.error("文件超过 20 MB 上限，请拆分后再上传。");
    return;
  }
  uploading.value = true;
  try {
    const summary = await api.uploadDocument(raw);
    docInfo.value = summary;
    docId.value = summary.doc_id;
    title.value = summary.filename.replace(/\.[^.]+$/, "");
    if (summary.warnings.length) {
      ElMessage.warning(`解析完成，但有 ${summary.warnings.length} 条提示，见文档库详情。`);
    } else {
      ElMessage.success(`已解析 ${summary.filename}，共 ${summary.char_count} 字。`);
    }
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "上传失败");
  } finally {
    uploading.value = false;
  }
}

async function runGenerate(): Promise<void> {
  if (!canGenerate.value) return;
  const payload = {
    doc_id: mode.value === "upload" ? docId.value : null,
    text: mode.value === "upload" ? null : text.value,
    title: title.value || (mode.value === "upload" ? "上传文档" : "粘贴的需求文本"),
    methods: methods.value,
    use_llm: useLlm.value,
    use_llm_in_design: useLlmInDesign.value,
    max_items: maxItems.value,
  };
  const output = await generate.run(payload);
  if (output) {
    ElMessage.success(
      `生成完成：共 ${output.suite.stats.total} 条用例，去重剔除 ${output.suite.stats.duplicate_removed} 条。`,
    );
  }
}

async function download(format: "excel" | "json"): Promise<void> {
  const suiteId = result.value?.suite.suite_id;
  if (!suiteId) return;
  const file = await api.exportSuite(suiteId, format);
  saveBlob(file.blob, file.filename || `${suiteId}.${format === "excel" ? "xlsx" : "json"}`);
}
</script>

<template>
  <div class="stack">
    <PageHead
      title="工作台"
      note="把需求文档变成可交付的用例集：输入需求 → 选择设计方法 → 生成 → 导出 Excel。未配置大模型时链路自动降级为规则引擎，仍然端到端可用。"
    />

    <div class="grid grid--work">
      <section class="card">
        <div class="card__head">
          <span class="card__title">需求输入</span>
          <div class="switch">
            <button
              type="button"
              class="switch__opt"
              :class="{ 'switch__opt--on': mode === 'text' }"
              @click="toggleMode('text')"
            >
              粘贴文本
            </button>
            <button
              type="button"
              class="switch__opt"
              :class="{ 'switch__opt--on': mode === 'upload' }"
              @click="toggleMode('upload')"
            >
              上传文档
            </button>
          </div>
        </div>

        <div class="card__body stack stack--tight">
          <template v-if="mode === 'text'">
            <label class="label" for="req-title">需求标题</label>
            <el-input id="req-title" v-model="title" maxlength="60" show-word-limit />

            <label class="label" for="req-text">需求正文</label>
            <el-input
              id="req-text"
              v-model="text"
              type="textarea"
              :rows="14"
              resize="vertical"
              placeholder="在此粘贴需求文本，例如：&#10;## 用户注册&#10;| 字段名 | 类型 | 必填 | 取值范围 |&#10;| 手机号 | 字符串 | 是 | 11位数字 |&#10;&#10;主流程 / 异常场景 / 业务规则 / 验收标准按标题书写，解析更准。"
            />
            <p class="hint dim">
              表格请保留 Tab 或 Markdown 列分隔；从 Word 直接复制时，字段约束表决定边界值与等价类的生成质量。
            </p>
          </template>

          <template v-else>
            <el-upload
              class="drop"
              drag
              :auto-upload="false"
              :show-file-list="false"
              accept=".docx,.pdf,.txt,.md,.csv,.json"
              :on-change="onFileChange"
            >
              <el-icon class="drop__icon"><UploadFilled /></el-icon>
              <p class="drop__title">把需求文档拖到这里，或点击选择</p>
              <p class="drop__hint dim">支持 docx / pdf / txt / md / csv / json，单文件不超过 20 MB</p>
            </el-upload>

            <div v-if="docInfo" class="docbox">
              <el-icon class="docbox__icon"><DocumentIcon /></el-icon>
              <div class="docbox__text">
                <p class="docbox__name">{{ docInfo.filename }}</p>
                <p class="docbox__meta mono">
                  {{ docInfo.doc_id }} · {{ formatBytes(docInfo.size_bytes) }} ·
                  {{ docInfo.char_count }} 字 · 解析器 {{ docInfo.parser }}
                </p>
              </div>
            </div>
            <p v-if="uploading" class="hint dim">正在上传并解析…</p>
          </template>
        </div>
      </section>

      <section class="card">
        <div class="card__head">
          <span class="card__title">生成设置</span>
        </div>
        <div class="card__body stack stack--tight">
          <div>
            <p class="label">设计方法</p>
            <el-checkbox-group v-model="methods" class="methods">
              <el-checkbox v-for="method in V1_METHODS" :key="method" :value="method">
                {{ methodLabel(method) }}
              </el-checkbox>
              <el-checkbox
                v-for="method in RESERVED_METHODS"
                :key="method"
                :value="method"
                disabled
              >
                {{ methodLabel(method) }}
                <span class="reserved">V2 预留</span>
              </el-checkbox>
            </el-checkbox-group>
          </div>

          <hr class="hairline" />

          <div class="field">
            <div class="field__head">
              <span class="label">最多解析条目</span>
              <span class="num field__value">{{ maxItems }}</span>
            </div>
            <el-slider v-model="maxItems" :min="1" :max="50" :step="1" />
            <p class="hint dim">
              从文档中最多抽取多少条需求。条目越多，边界值用例越多，生成耗时越长。
            </p>
          </div>

          <hr class="hairline" />

          <div class="toggles">
            <label class="toggle">
              <el-switch v-model="useLlm" />
              <span>
                <span class="toggle__title">使用大模型辅助解析</span>
                <span class="toggle__hint dim">失败或未配置 Key 时自动降级为规则引擎，并在结果里标注</span>
              </span>
            </label>
            <label class="toggle">
              <el-switch v-model="useLlmInDesign" />
              <span>
                <span class="toggle__title">生成阶段也调用大模型</span>
                <span class="toggle__hint dim">主要用于补齐场景法用例，耗时更长</span>
              </span>
            </label>
          </div>

          <el-button
            type="primary"
            size="large"
            :loading="generate.loading.value"
            :disabled="!canGenerate"
            @click="runGenerate"
          >
            {{ generate.loading.value ? "正在生成…" : "一键生成用例" }}
          </el-button>
          <p v-if="methodError" class="hint hint--bad">{{ methodError }}</p>
          <p v-else-if="!canGenerate" class="hint dim">
            {{ mode === "upload" ? "请先上传并解析一份文档。" : "请先粘贴需求正文。" }}
          </p>
        </div>
      </section>
    </div>

    <ErrorNote v-if="generate.error.value" :error="generate.error.value" />

    <template v-if="result">
      <StatStrip :items="statItems" />

      <div v-if="result.warnings.length" class="warns">
        <p class="warns__title">生成过程有 {{ result.warnings.length }} 条提示</p>
        <ul>
          <li v-for="(warning, index) in result.warnings.slice(0, 8)" :key="index">{{ warning }}</li>
        </ul>
      </div>

      <div class="row row--wrap">
        <el-button
          type="primary"
          :icon="Download"
          :loading="exportExcel.loading.value"
          @click="exportExcel.run"
        >
          导出 Excel
        </el-button>
        <el-button :icon="Download" :loading="exportJson.loading.value" @click="exportJson.run">
          导出 JSON
        </el-button>
        <el-button @click="router.push(`/suites/${result.suite.suite_id}`)">打开用例集详情</el-button>
        <el-button @click="router.push(`/documents/${result.requirement_doc.doc_id}/requirement`)">
          查看结构化需求
        </el-button>
      </div>

      <CaseTable
        :cases="result.suite.cases"
        :items="itemsIndex"
        :doc-id="result.requirement_doc.doc_id"
      />

      <ErrorNote v-if="exportExcel.error.value" :error="exportExcel.error.value" />
      <ErrorNote v-if="exportJson.error.value" :error="exportJson.error.value" />
    </template>
  </div>
</template>

<style scoped>
.switch {
  display: inline-flex;
  border: 1px solid var(--rule-strong);
  border-radius: var(--radius);
  overflow: hidden;
}

.switch__opt {
  appearance: none;
  border: 0;
  background: var(--card);
  padding: 4px 12px;
  font: inherit;
  font-size: var(--fs-xs);
  color: var(--ink-2);
  cursor: pointer;
}

.switch__opt + .switch__opt {
  border-left: 1px solid var(--rule);
}

.switch__opt--on {
  background: var(--cabinet);
  color: var(--cabinet-ink);
}

.drop {
  display: block;
}

.drop :deep(.el-upload-dragger) {
  background: var(--card);
  border: 1px dashed var(--rule-strong);
  border-radius: var(--radius);
  padding: var(--s6) var(--s4);
  transition: border-color var(--dur-fast) var(--ease), background-color var(--dur-fast) var(--ease);
}

.drop :deep(.el-upload-dragger:hover),
.drop :deep(.el-upload-dragger.is-dragover) {
  border-color: var(--stamp);
  background: var(--stamp-wash);
}

.drop__icon {
  font-size: 30px;
  color: var(--ink-3);
}

.drop__title {
  margin-top: var(--s2);
  font-size: var(--fs-base);
  color: var(--ink);
}

.drop__hint {
  margin-top: 2px;
  font-size: var(--fs-xs);
}

.docbox {
  display: flex;
  align-items: center;
  gap: var(--s3);
  padding: var(--s3);
  border: 1px solid var(--rule);
  border-radius: var(--radius);
  background: var(--paper-sunk);
}

.docbox__icon {
  font-size: 20px;
  color: var(--ink-3);
}

.docbox__name {
  font-size: var(--fs-sm);
  font-weight: 500;
  color: var(--ink);
}

.docbox__meta {
  font-size: var(--fs-xs);
  color: var(--ink-3);
}

.methods {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: var(--s2);
}

.methods :deep(.el-checkbox) {
  height: auto;
}

.reserved {
  margin-left: 4px;
  font-size: 10px;
  color: var(--ink-4);
  border: 1px solid var(--rule-strong);
  border-radius: var(--radius-sm);
  padding: 0 4px;
}

.field__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.field__value {
  font-size: var(--fs-md);
  color: var(--ink);
}

.toggles {
  display: flex;
  flex-direction: column;
  gap: var(--s3);
}

.toggle {
  display: flex;
  align-items: flex-start;
  gap: var(--s3);
  cursor: pointer;
}

.toggle__title {
  display: block;
  font-size: var(--fs-base);
  color: var(--ink);
}

.toggle__hint {
  display: block;
  font-size: var(--fs-xs);
  line-height: 1.5;
}

.hint {
  font-size: var(--fs-xs);
  line-height: 1.55;
}

.hint--bad {
  color: var(--danger);
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
</style>
