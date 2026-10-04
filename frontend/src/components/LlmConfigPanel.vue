<script setup lang="ts">
/**
 * 大模型配置面板。
 *
 * 与后端约定：界面保存的是「运行时覆盖」（storage/data/llm_config.json），
 * 优先级高于 .env 基线，可一键恢复；密钥只存服务端、回显掩码。
 */
import { computed, onMounted, reactive, ref } from "vue";
import { Check, Connection, Refresh } from "@element-plus/icons-vue";

import { api } from "@/api";
import type { LLMConfigInfo, LLMConfigPayload, LLMModelOption, LLMTestResult } from "@/api";
import { confirmAction, notice } from "@/composables/useNotice";
import { useHealthStore } from "@/stores/health";

const health = useHealthStore();

const config = ref<LLMConfigInfo | null>(null);
const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const resetting = ref(false);
const loadingModels = ref(false);

const apiKeyInput = ref("");
const apiKeyTouched = ref(false);
const clearKey = ref(false);
const remoteModels = ref<LLMModelOption[]>([]);
const testResult = ref<LLMTestResult | null>(null);

const form = reactive({
  provider: "",
  model: "",
  base_url: "",
  timeout: 60,
  max_retries: 2,
  temperature: 0.2,
  max_tokens: 4096,
});

const providers = computed(() => config.value?.providers ?? []);
const currentProvider = computed(
  () => providers.value.find((item) => item.name === form.provider) ?? null,
);
const isRuleOnly = computed(() => form.provider === "none" || form.provider === "fake");
const needsKey = computed(() => currentProvider.value?.requires_key === true);
const needsBaseUrl = computed(() => currentProvider.value?.requires_base_url === true);
const keyReady = computed(
  () =>
    (config.value?.api_key_configured ?? false) ||
    (apiKeyTouched.value && apiKeyInput.value.trim().length > 0),
);

const modelOptions = computed<LLMModelOption[]>(() => {
  const seen = new Set<string>();
  const list: LLMModelOption[] = [];
  for (const item of [...(currentProvider.value?.models ?? []), ...remoteModels.value]) {
    if (!item.value || seen.has(item.value)) continue;
    seen.add(item.value);
    list.push(item);
  }
  return list;
});

const sourceLabel = computed(() => (config.value?.source === "runtime" ? "界面覆盖" : ".env 基线"));
const sourceTitle = computed(() =>
  config.value?.source === "runtime"
    ? "当前生效值来自本页保存的界面覆盖（storage/data/llm_config.json），优先级高于 .env"
    : "当前生效值来自 .env / 环境变量基线（后端固定配置）",
);
const statusLabel = computed(() => (config.value?.available ? "已就绪" : "未启用 / 降级"));
const statusTitle = computed(
  () => config.value?.degraded_reason || "当前配置可以真实调用大模型。",
);
const keyHint = computed(() => {
  const info = config.value;
  if (!info) return "";
  return info.api_key_configured
    ? `当前已配置：${info.api_key_masked}，留空表示不修改。`
    : "当前未配置 Key，填写后才能调用大模型。";
});
const baseUrlHint = computed(() =>
  needsBaseUrl.value
    ? "OpenAI 兼容端点根地址，服务端会请求 {base_url}/chat/completions。"
    : currentProvider.value?.default_base_url
      ? `默认端点：${currentProvider.value.default_base_url}`
      : "该厂商无需填写接口地址。",
);
const apiKeyPlaceholder = computed(() =>
  config.value?.api_key_configured
    ? `已配置 ${config.value.api_key_masked}（留空不修改）`
    : "粘贴 API Key，例如 sk-...",
);

/** 前端必填校验：红色提示 + 禁用保存/测试按钮，避免提交后才报错。 */
const formError = computed(() => {
  if (!config.value) return "";
  if (!form.provider) return "请选择大模型厂商。";
  if (needsKey.value && clearKey.value)
    return "已勾选「清除已保存的 Key」，但该厂商必须提供 Key；请填写新 Key 或改用「纯规则引擎」。";
  if (needsKey.value && !keyReady.value) return "该厂商需要 API Key，请填写后再保存。";
  if (needsBaseUrl.value && !form.base_url.trim())
    return "OpenAI 兼容端点需要填写接口地址（如 https://api.deepseek.com）。";
  if (!isRuleOnly.value && !form.model.trim()) return "请选择或填写模型名称。";
  return "";
});

function applyConfig(info: LLMConfigInfo): void {
  config.value = info;
  form.provider = info.provider;
  form.model = info.model;
  form.base_url = info.base_url;
  form.timeout = info.timeout;
  form.max_retries = info.max_retries;
  form.temperature = info.temperature;
  form.max_tokens = info.max_tokens;
  apiKeyInput.value = "";
  apiKeyTouched.value = false;
  clearKey.value = false;
  remoteModels.value = [];
}

async function load(): Promise<void> {
  loading.value = true;
  try {
    applyConfig(await api.llmConfig());
  } catch (err) {
    notice.error(err, "读取大模型配置失败。");
  } finally {
    loading.value = false;
  }
}

/** 切换厂商时带出该厂商的默认端点与默认模型，减少手填。 */
function onProviderChange(name: string): void {
  const option = providers.value.find((item) => item.name === name);
  remoteModels.value = [];
  testResult.value = null;
  if (!option) return;
  form.model = option.default_model;
  form.base_url = option.default_base_url;
}

function buildPayload(withRetries = true): LLMConfigPayload {
  const payload: LLMConfigPayload = {
    provider: form.provider,
    timeout: form.timeout,
    temperature: form.temperature,
    max_tokens: form.max_tokens,
  };
  if (withRetries) payload.max_retries = form.max_retries;
  if (form.model.trim()) payload.model = form.model.trim();
  if (form.base_url.trim()) payload.base_url = form.base_url.trim();
  if (clearKey.value) payload.api_key = "";
  else if (apiKeyTouched.value && apiKeyInput.value.trim()) payload.api_key = apiKeyInput.value.trim();
  return payload;
}

async function fetchModels(): Promise<void> {
  loadingModels.value = true;
  try {
    const data = await api.llmModels(form.provider);
    if (data.source === "remote") {
      remoteModels.value = data.models;
      notice.success(`已从厂商接口拉取 ${data.models.length} 个模型。`);
    } else {
      notice.info(data.message || "已使用内置模型列表。");
    }
  } catch (err) {
    notice.error(err, "拉取模型列表失败，已保留内置列表。");
  } finally {
    loadingModels.value = false;
  }
}

async function save(): Promise<void> {
  if (formError.value) {
    notice.warn(formError.value);
    return;
  }
  const label = currentProvider.value?.label ?? form.provider;
  const confirmed = await confirmAction(
    `将把大模型切换为「${label} · ${form.model || "默认模型"}」，保存后立即对后续解析 / 生成生效。是否继续？`,
    "保存大模型配置",
    "保存并生效",
  );
  if (!confirmed) return;
  saving.value = true;
  try {
    applyConfig(await api.saveLlmConfig(buildPayload()));
    await health.load(true);
    notice.done("大模型配置已保存", `${label} · ${config.value?.model || "默认模型"} 已生效。`);
  } catch (err) {
    notice.error(err, "保存失败，请检查参数后重试。");
  } finally {
    saving.value = false;
  }
}

async function runTest(): Promise<void> {
  if (formError.value) {
    notice.warn(formError.value);
    return;
  }
  testing.value = true;
  testResult.value = null;
  try {
    const result = await api.testLlmConfig(buildPayload(false));
    testResult.value = result;
    if (result.ok) {
      notice.success(`连接成功（${result.model || result.provider}，${result.elapsed_ms} ms）。`);
    } else {
      notice.error(result.message || "连接失败，请检查 Key / 端点 / 模型。");
    }
  } catch (err) {
    notice.error(err, "测试连接失败。");
  } finally {
    testing.value = false;
  }
}

async function reset(): Promise<void> {
  const confirmed = await confirmAction(
    "将清除界面上的覆盖配置，恢复 .env 中的固定配置（后端基线）。是否继续？",
    "恢复 .env 配置",
    "恢复",
  );
  if (!confirmed) return;
  resetting.value = true;
  try {
    applyConfig(await api.resetLlmConfig());
    await health.load(true);
    notice.success("已恢复 .env 配置。");
  } catch (err) {
    notice.error(err, "恢复失败，请稍后重试。");
  } finally {
    resetting.value = false;
  }
}

onMounted(() => {
  void load();
});
</script>

<template>
  <section class="card">
    <div class="card__head">
      <span class="card__title">大模型配置</span>
      <span class="tags">
        <span class="tag" :class="config?.source === 'runtime' ? 'tag--stamp' : 'tag--plain'" :title="sourceTitle">
          {{ sourceLabel }}
        </span>
        <span
          class="tag"
          :class="config?.available ? 'tag--ok' : 'tag--warn'"
          :title="statusTitle"
        >
          {{ statusLabel }}
        </span>
      </span>
    </div>

    <div class="card__body">
      <p class="hint">
        在这里切换厂商与模型，保存后立即生效、无需重启。优先级：<span class="mono">界面覆盖</span> &gt;
        <span class="mono">.env</span>，随时可一键恢复；密钥仅保存在服务端，回显为掩码。
      </p>

      <el-skeleton v-if="loading && !config" :rows="4" animated />

      <template v-else-if="config">
        <div class="form">
          <label class="field">
            <span class="field__label" title="选择大模型厂商，切换后自动带出默认端点与默认模型">
              厂商<span v-if="needsKey" class="req" title="该厂商必须提供 API Key">*</span>
            </span>
            <el-select
              v-model="form.provider"
              class="field__control"
              placeholder="请选择厂商"
              @change="onProviderChange"
            >
              <el-option
                v-for="item in providers"
                :key="item.name"
                :value="item.name"
                :label="item.label"
              >
                <span class="opt">
                  <span>{{ item.label }}</span>
                  <span class="opt__note">{{ item.description }}</span>
                </span>
              </el-option>
            </el-select>
          </label>

          <label class="field">
            <span class="field__label" title="候选模型来自内置目录或厂商 /models 接口；也可直接输入自定义模型名">
              模型<span v-if="!isRuleOnly" class="req" title="必填">*</span>
            </span>
            <span class="field__control field__control--row">
              <el-select
                v-model="form.model"
                class="grow"
                filterable
                allow-create
                default-first-option
                :disabled="isRuleOnly"
                :placeholder="currentProvider?.allow_custom_model ? '选择或输入模型名' : '选择模型'"
              >
                <el-option
                  v-for="item in modelOptions"
                  :key="item.value"
                  :value="item.value"
                  :label="item.label || item.value"
                />
              </el-select>
              <el-button
                :icon="Refresh"
                :loading="loadingModels"
                :disabled="isRuleOnly"
                title="从厂商 /models 接口拉取可用模型，失败时回退内置列表"
                @click="fetchModels"
              >
                拉取模型
              </el-button>
            </span>
          </label>

          <label class="field field--wide">
            <span class="field__label" title="OpenAI 兼容端点根地址，服务端请求 {base_url}/chat/completions">
              接口地址 base_url
            </span>
            <el-input
              v-model="form.base_url"
              class="mono"
              :disabled="isRuleOnly || !needsBaseUrl"
              placeholder="https://api.deepseek.com"
            />
            <span class="field__hint">{{ baseUrlHint }}</span>
          </label>

          <label class="field field--wide">
            <span class="field__label" title="只在服务端保存；界面仅显示掩码，不显示明文">
              API Key<span v-if="needsKey" class="req" title="必填">*</span>
            </span>
            <el-input
              v-model="apiKeyInput"
              type="password"
              show-password
              :disabled="!needsKey"
              :placeholder="apiKeyPlaceholder"
              @input="apiKeyTouched = true"
            />
            <span class="field__hint">{{ keyHint }}</span>
            <el-checkbox
              v-model="clearKey"
              class="field__check"
              title="勾选后保存会删除服务端已保存的 Key，并回落到 .env 的 Key"
            >
              清除已保存的 Key
            </el-checkbox>
          </label>

          <label class="field">
            <span class="field__label" title="单次请求超时时间（秒）">超时（秒）</span>
            <el-input-number v-model="form.timeout" :min="5" :max="600" :step="5" controls-position="right" />
          </label>

          <label class="field">
            <span class="field__label" title="大模型返回非法 JSON 时的自动修复重试次数">重试次数</span>
            <el-input-number v-model="form.max_retries" :min="0" :max="10" controls-position="right" />
          </label>

          <label class="field">
            <span class="field__label" title="越低输出越稳定，建议 0.1 ~ 0.3">温度 temperature</span>
            <el-input-number
              v-model="form.temperature"
              :min="0"
              :max="2"
              :step="0.1"
              :precision="1"
              controls-position="right"
            />
          </label>

          <label class="field">
            <span class="field__label" title="单次回复的最大 token 数">最大 tokens</span>
            <el-input-number v-model="form.max_tokens" :min="256" :max="131072" :step="256" controls-position="right" />
          </label>
        </div>

        <p v-if="formError" class="error" title="按提示修正后即可保存或测试">⚠ {{ formError }}</p>

        <div class="actions">
          <el-button
            type="primary"
            :icon="Check"
            :loading="saving"
            :disabled="!!formError"
            title="保存到服务端并立即对后续解析 / 生成生效"
            @click="save"
          >
            保存配置
          </el-button>
          <el-button
            :icon="Connection"
            :loading="testing"
            :disabled="!!formError"
            title="用当前表单值发一次真实请求，验证 Key / 端点 / 模型是否可用"
            @click="runTest"
          >
            测试连接
          </el-button>
          <el-button
            :loading="resetting"
            title="清除界面覆盖，恢复 .env 中的后端固定配置"
            @click="reset"
          >
            恢复 .env 配置
          </el-button>
        </div>

        <el-alert
          v-if="testResult"
          class="test"
          :type="testResult.ok ? 'success' : 'error'"
          :closable="false"
          show-icon
          :title="
            testResult.ok
              ? `连接成功：${testResult.model || testResult.provider}（${testResult.elapsed_ms} ms）`
              : `连接失败：${testResult.message}`
          "
        >
          <template v-if="testResult.reply" #default>模型回复：{{ testResult.reply }}</template>
        </el-alert>
      </template>
    </div>
  </section>
</template>

<style scoped>
.tags {
  display: flex;
  gap: var(--s2);
}

.tag {
  font-size: var(--fs-xs);
  border-radius: var(--radius-sm);
  padding: 1px 7px;
  border: 1px solid transparent;
}

.tag--plain {
  color: var(--ink-3);
  background: var(--paper-sunk);
  border-color: var(--rule-strong);
}

.tag--stamp {
  color: var(--stamp-deep);
  background: var(--stamp-wash);
  border-color: rgba(26, 127, 169, 0.3);
}

.tag--ok {
  color: var(--ok);
  background: var(--ok-wash);
  border-color: rgba(44, 106, 76, 0.3);
}

.tag--warn {
  color: var(--warn);
  background: var(--warn-wash);
  border-color: rgba(138, 97, 20, 0.3);
}

.hint {
  margin: 0 0 var(--s4);
  font-size: var(--fs-sm);
  color: var(--ink-3);
  line-height: var(--lh-snug);
}

.form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--s4);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--s2);
  min-width: 0;
}

.field--wide {
  grid-column: 1 / -1;
}

.field__label {
  font-size: var(--fs-sm);
  color: var(--ink-2);
}

.field__control {
  width: 100%;
}

.field__control--row {
  display: flex;
  gap: var(--s2);
}

.grow {
  flex: 1;
  min-width: 0;
}

.field__hint {
  font-size: var(--fs-xs);
  color: var(--ink-4);
}

.field__check {
  align-self: flex-start;
}

.req {
  color: var(--danger);
  margin-left: 2px;
}

.error {
  margin: var(--s4) 0 0;
  font-size: var(--fs-sm);
  color: var(--danger);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--s2);
  margin-top: var(--s4);
}

.test {
  margin-top: var(--s4);
}

.opt {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--s3);
}

.opt__note {
  font-size: var(--fs-xs);
  color: var(--ink-4);
}
</style>
