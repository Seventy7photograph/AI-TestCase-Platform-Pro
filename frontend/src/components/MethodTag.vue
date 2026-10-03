<script setup lang="ts">
import { computed } from "vue";

import { METHOD_CODES, methodLabel } from "@/utils/labels";

const props = defineProps<{ value: string; full?: boolean }>();

const label = computed(() => methodLabel(props.value));
const code = computed(() => METHOD_CODES[props.value] ?? "—");
</script>

<template>
  <span class="mtag" :title="label">
    <span class="mtag__code mono">{{ code }}</span>
    <span class="mtag__label">{{ full ? label : label.replace(/划分|分析/, "") }}</span>
  </span>
</template>

<style scoped>
.mtag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}

.mtag__code {
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.04em;
  color: var(--ink-3);
  background: var(--paper-sunk);
  border: 1px solid var(--rule-strong);
  border-radius: var(--radius-sm);
  padding: 0 3px;
  line-height: 15px;
}

.mtag__label {
  font-size: var(--fs-xs);
  color: var(--ink-2);
}
</style>
