<script setup lang="ts">
import { RouterView } from "vue-router";

import CabinetRail from "./CabinetRail.vue";
import TopBar from "./TopBar.vue";
</script>

<template>
  <div class="shell">
    <CabinetRail />
    <div class="shell__body">
      <TopBar />
      <main class="shell__content">
        <RouterView v-slot="{ Component }">
          <component :is="Component" />
        </RouterView>
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: var(--rail-w) minmax(0, 1fr);
  min-height: 100vh;
  background: var(--paper);
}

.shell__body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.shell__content {
  flex: 1 1 auto;
  min-width: 0;
  max-width: 100%;
  padding: var(--s6) var(--s7) var(--s7);
}

@media (max-width: 900px) {
  .shell {
    grid-template-columns: minmax(0, 1fr);
  }

  .shell__content {
    padding: var(--s4) var(--s4) var(--s6);
  }
}
</style>
