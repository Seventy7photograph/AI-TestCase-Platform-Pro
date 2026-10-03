<script setup lang="ts">
defineProps<{
  title: string;
  note?: string;
  backTo?: string;
  backLabel?: string;
}>();
</script>

<template>
  <header class="head">
    <RouterLink v-if="backTo" :to="backTo" class="head__back">
      ← {{ backLabel || "返回" }}
    </RouterLink>
    <div class="head__main">
      <div class="head__text">
        <h1>{{ title }}</h1>
        <p v-if="note" class="head__note">{{ note }}</p>
      </div>
      <div class="head__actions">
        <slot name="actions" />
      </div>
    </div>
  </header>
</template>

<style scoped>
.head {
  display: flex;
  flex-direction: column;
  gap: var(--s2);
  /* 标题上方的留白多于下方 */
  margin-bottom: var(--s6);
}

.head__back {
  font-size: var(--fs-xs);
  color: var(--ink-3);
  text-decoration: none;
  width: fit-content;
}

.head__back:hover {
  color: var(--stamp-deep);
}

.head__main {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--s5);
  flex-wrap: wrap;
}

.head__text {
  min-width: 0;
}

.head__note {
  margin-top: var(--s2);
  max-width: 68ch;
  font-size: var(--fs-sm);
  color: var(--ink-3);
}

.head__actions {
  display: flex;
  align-items: center;
  gap: var(--s3);
  flex-wrap: wrap;
}
</style>
