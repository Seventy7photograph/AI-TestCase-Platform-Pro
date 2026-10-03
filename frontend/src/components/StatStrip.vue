<script setup lang="ts">
export interface StatItem {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "default" | "accent" | "good" | "warn" | "bad";
  mono?: boolean;
}

defineProps<{ items: StatItem[] }>();
</script>

<template>
  <dl class="strip">
    <div v-for="item in items" :key="item.label" class="strip__cell">
      <dt class="strip__label label">{{ item.label }}</dt>
      <dd
        class="strip__value"
        :class="[
          item.mono === false ? 'strip__value--ui' : 'num',
          item.tone && item.tone !== 'default' ? `strip__value--${item.tone}` : '',
        ]"
      >
        {{ item.value }}
      </dd>
      <dd v-if="item.hint" class="strip__hint">{{ item.hint }}</dd>
    </div>
  </dl>
</template>

<style scoped>
.strip {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(0, 1fr);
  margin: 0;
  background: var(--card);
  border: 1px solid var(--card-edge);
  border-radius: var(--radius);
  overflow: hidden;
}

.strip__cell {
  padding: var(--s3) var(--s4);
  min-width: 0;
}

.strip__cell + .strip__cell {
  border-left: 1px solid var(--rule);
}

.strip__label {
  display: block;
  margin: 0;
}

.strip__value {
  margin: 2px 0 0;
  font-size: var(--fs-lg);
  font-weight: 500;
  line-height: 1.2;
  color: var(--ink);
}

.strip__value--ui {
  font-family: var(--font-ui);
  letter-spacing: 0;
}

.strip__value--accent {
  color: var(--stamp-deep);
}

.strip__value--good {
  color: var(--ok);
}

.strip__value--warn {
  color: var(--warn);
}

.strip__value--bad {
  color: var(--danger);
}

.strip__hint {
  margin: 3px 0 0;
  font-size: 11px;
  line-height: 1.45;
  color: var(--ink-4);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@media (max-width: 1100px) {
  .strip {
    grid-auto-flow: row;
    grid-auto-columns: auto;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }

  .strip__cell + .strip__cell {
    border-left: 0;
    border-top: 1px solid var(--rule);
  }
}
</style>
