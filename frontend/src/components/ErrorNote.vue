<script setup lang="ts">
import { ApiError } from "@/api";

defineProps<{ error: ApiError | Error | null }>();
</script>

<template>
  <div v-if="error" class="err" role="alert">
    <p class="err__title">{{ error.message }}</p>
    <p v-if="error instanceof ApiError && error.code" class="err__code mono">
      错误码 {{ error.code }}
    </p>
  </div>
</template>

<style scoped>
.err {
  padding: var(--s3) var(--s4);
  background: var(--danger-wash);
  border: 1px solid rgba(157, 42, 33, 0.28);
  border-radius: var(--radius);
}

.err__title {
  font-size: var(--fs-sm);
  color: var(--danger);
  font-weight: 500;
}

.err__code {
  margin-top: 2px;
  font-size: var(--fs-xs);
  color: var(--ink-3);
}
</style>
