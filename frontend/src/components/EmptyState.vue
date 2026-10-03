<script setup lang="ts">
defineProps<{ title: string; hint?: string }>();
</script>

<template>
  <div class="empty">
    <div class="empty__frame" aria-hidden="true"></div>
    <p class="empty__title">{{ title }}</p>
    <p v-if="hint" class="empty__hint">{{ hint }}</p>
    <div class="empty__actions">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--s3);
  padding: var(--s7) var(--s5);
  text-align: center;
}

/* 一张空白的索引卡 */
.empty__frame {
  width: 96px;
  height: 60px;
  border: 1px solid var(--rule-strong);
  border-radius: var(--radius);
  background: var(--card);
  position: relative;
}

.empty__frame::after {
  content: "";
  position: absolute;
  left: 10px;
  right: 10px;
  top: 34px;
  border-top: 1px solid var(--rule);
  box-shadow: 0 6px 0 var(--rule), 0 12px 0 var(--rule);
}

.empty__title {
  font-size: var(--fs-md);
  font-weight: 600;
  color: var(--ink);
}

.empty__hint {
  max-width: 52ch;
  font-size: var(--fs-sm);
  color: var(--ink-3);
}
</style>
