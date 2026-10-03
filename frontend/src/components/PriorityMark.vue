<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ value: string; showLabel?: boolean }>();

/* 形状与文字同时编码，不靠颜色单独区分优先级 */
const shape = computed(() => (props.value || "P3").toLowerCase());
</script>

<template>
  <span class="pri" :class="`pri--${shape}`">
    <span class="pri__mark" aria-hidden="true"></span>
    <span class="pri__text mono">{{ value }}</span>
    <span v-if="showLabel" class="pri__name">{{ {
      P0: "阻断", P1: "严重", P2: "一般", P3: "轻微",
    }[value] ?? "" }}</span>
  </span>
</template>

<style scoped>
.pri {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}

.pri__mark {
  width: 9px;
  height: 9px;
  border-radius: 1px;
  flex: none;
  border: 1px solid transparent;
}

.pri__text {
  font-size: var(--fs-xs);
  font-weight: 500;
  color: var(--ink-2);
}

.pri__name {
  font-size: 11px;
  color: var(--ink-4);
}

.pri--p0 .pri__mark {
  background: var(--danger);
  border-color: var(--danger);
}

.pri--p1 .pri__mark {
  background: var(--warn);
  border-color: var(--warn);
}

.pri--p2 .pri__mark {
  border-color: var(--ink-3);
}

.pri--p3 .pri__mark {
  border-style: dotted;
  border-color: var(--ink-4);
}
</style>
