import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { api } from "@/api";
import type { HealthInfo, IntegrationInfo } from "@/api";

export const useHealthStore = defineStore("health", () => {
  const info = ref<HealthInfo | null>(null);
  const integrations = ref<IntegrationInfo[]>([]);
  const loading = ref(false);
  const error = ref<string>("");

  async function load(force = false): Promise<void> {
    if (loading.value) return;
    if (info.value && !force) return;
    loading.value = true;
    error.value = "";
    try {
      const [health, integrationList] = await Promise.all([
        api.health(),
        api.integrations().catch(() => [] as IntegrationInfo[]),
      ]);
      info.value = health;
      integrations.value = integrationList;
    } catch (err) {
      error.value = err instanceof Error ? err.message : "无法读取服务状态";
    } finally {
      loading.value = false;
    }
  }

  const reachable = computed(() => info.value !== null);
  const llmReady = computed(() => info.value?.llm_available === true);
  const llmSourceLabel = computed(() =>
    info.value?.llm_source === "runtime" ? "界面覆盖" : ".env 基线",
  );
  const llmLabel = computed(() => {
    if (!info.value) return "未连接";
    if (info.value.llm_available) {
      return `${info.value.llm_provider}${info.value.llm_model ? " · " + info.value.llm_model : ""}`;
    }
    return "规则引擎（未启用大模型）";
  });

  return { info, integrations, loading, error, load, reachable, llmReady, llmLabel, llmSourceLabel };
});
