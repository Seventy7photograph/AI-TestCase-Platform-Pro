<script setup lang="ts">
import { computed } from "vue";

import { useDensity } from "@/composables/useDensity";
import type { Density } from "@/composables/useDensity";
import { useHealthStore } from "@/stores/health";

const health = useHealthStore();
const { density, setDensity } = useDensity();

const levels: { value: Density; label: string }[] = [
  { value: "compact", label: "紧凑" },
  { value: "cozy", label: "标准" },
  { value: "relaxed", label: "宽松" },
];

const statusText = computed(() => {
  if (health.loading && !health.info) return "连接中";
  if (!health.reachable) return "未连接";
  return health.info?.app_name ? `已连接 · v${health.info.version}` : "已连接";
});

const statusTone = computed(() => {
  if (!health.reachable) return "bad";
  return health.llmReady ? "good" : "warn";
});

const statusHint = computed(() => {
  if (health.loading && !health.info) return "正在请求 /api/v1/health";
  if (!health.reachable) {
    return health.error || "无法连接后端服务，请确认已执行 python run.py";
  }
  return health.llmReady
    ? `已连接 · 推理引擎 ${health.llmLabel}`
    : `已连接，但未启用大模型：${health.info?.llm_degraded_reason || "链路自动降级为规则引擎"}`;
});
</script>

<template>
  <header class="bar">
    <div class="bar__left">
      <span class="bar__endpoint mono">/api/v1</span>
      <span
        class="bar__status"
        :class="`bar__status--${statusTone}`"
        :title="statusHint"
      >
        <span class="bar__dot" aria-hidden="true"></span>
        {{ statusText }}
      </span>
      <span v-if="health.reachable" class="bar__llm" :title="health.llmLabel">
        {{ health.llmLabel }}
      </span>
    </div>

    <div class="bar__right">
      <span class="label" id="density-label">表格密度</span>
      <div
        class="segmented"
        role="radiogroup"
        aria-labelledby="density-label"
      >
        <button
          v-for="level in levels"
          :key="level.value"
          type="button"
          role="radio"
          class="segmented__opt"
          :class="{ 'segmented__opt--on': density === level.value }"
          :aria-checked="density === level.value"
          :title="`切换为${level.label}表格密度`"
          @click="setDensity(level.value)"
        >
          {{ level.label }}
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s4);
  flex-wrap: wrap;
  height: var(--topbar-h);
  padding: 0 var(--s7);
  background: var(--card);
  border-bottom: 1px solid var(--rule);
  position: sticky;
  top: 0;
  z-index: 20;
}

.bar__left,
.bar__right {
  display: flex;
  align-items: center;
  gap: var(--s3);
  min-width: 0;
}

.bar__endpoint {
  font-size: var(--fs-xs);
  color: var(--ink-3);
}

.bar__status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-xs);
  color: var(--ink-2);
}

.bar__dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: var(--ink-4);
}

.bar__status--good .bar__dot {
  background: var(--ok);
}

.bar__status--warn .bar__dot {
  background: var(--warn);
}

.bar__status--bad .bar__dot {
  background: var(--danger);
}

.bar__llm {
  font-size: var(--fs-xs);
  color: var(--ink-3);
  padding-left: var(--s3);
  border-left: 1px solid var(--rule);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 28ch;
}

.segmented {
  display: inline-flex;
  border: 1px solid var(--rule-strong);
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--card);
}

.segmented__opt {
  appearance: none;
  border: 0;
  background: transparent;
  padding: 4px 10px;
  font: inherit;
  font-size: var(--fs-xs);
  color: var(--ink-2);
  cursor: pointer;
  transition: background-color var(--dur-fast) var(--ease),
    color var(--dur-fast) var(--ease);
}

.segmented__opt + .segmented__opt {
  border-left: 1px solid var(--rule);
}

.segmented__opt:hover {
  background: var(--paper-sunk);
}

.segmented__opt--on {
  background: var(--cabinet);
  color: var(--cabinet-ink);
}

@media (max-width: 900px) {
  .bar {
    padding: 0 var(--s4);
    height: auto;
    padding-block: var(--s2);
  }

  .bar__llm {
    display: none;
  }
}
</style>
