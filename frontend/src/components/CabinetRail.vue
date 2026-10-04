<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import { useHealthStore } from "@/stores/health";

interface Drawer {
  nav: string;
  to: string;
  label: string;
  hint: string;
}

const drawers: Drawer[] = [
  { nav: "workbench", to: "/", label: "工作台", hint: "需求 → 用例" },
  { nav: "documents", to: "/documents", label: "文档与需求", hint: "上传 · 解析" },
  { nav: "suites", to: "/suites", label: "用例集", hint: "浏览 · 导出" },
  { nav: "capability", to: "/capability", label: "运行状态", hint: "引擎 · 接口" },
];

const route = useRoute();
const health = useHealthStore();
const activeNav = computed(() => String(route.meta.nav ?? "workbench"));
</script>

<template>
  <aside class="rail">
    <div class="rail__brand">
      <p class="rail__mark">AI 测试用例生成助手</p>
      <p class="rail__sub mono">需求 → 等价类 / 边界值 / 场景法 → 用例集</p>
    </div>

    <nav class="rail__nav" aria-label="主要区域">
      <RouterLink
        v-for="drawer in drawers"
        :key="drawer.nav"
        :to="drawer.to"
        class="drawer"
        :class="{ 'drawer--open': activeNav === drawer.nav }"
        :aria-current="activeNav === drawer.nav ? 'page' : undefined"
        :title="`${drawer.label} · ${drawer.hint}`"
      >
        <span class="drawer__label">{{ drawer.label }}</span>
        <span class="drawer__hint mono">{{ drawer.hint }}</span>
      </RouterLink>
    </nav>

    <div class="rail__foot">
      <p class="rail__footLabel label">推理引擎</p>
      <p class="rail__footValue">{{ health.llmLabel }}</p>
      <p
        v-if="!health.reachable"
        class="rail__footWarn"
        :title="health.error || '正在读取服务状态'"
      >
        {{ health.error || "正在读取服务状态…" }}
      </p>
      <p
        v-else-if="!health.llmReady"
        class="rail__footWarn"
        title="未配置 LLM_API_KEY 时自动降级为纯规则引擎，功能仍可用"
      >
        未配置 API Key，链路仍端到端可用
      </p>
    </div>
  </aside>
</template>

<style scoped>
.rail {
  display: flex;
  flex-direction: column;
  gap: var(--s5);
  position: sticky;
  top: 0;
  height: 100vh;
  padding: var(--s5) 0 var(--s5) var(--s4);
  background: var(--cabinet);
  color: var(--cabinet-ink);
}

.rail__brand {
  padding-right: var(--s4);
}

.rail__mark {
  font-size: var(--fs-md);
  font-weight: 600;
  letter-spacing: -0.01em;
  line-height: var(--lh-snug);
  color: var(--cabinet-ink);
}

.rail__sub {
  margin-top: var(--s1);
  font-size: 11px;
  line-height: 1.5;
  color: var(--cabinet-ink-2);
}

.rail__nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-right: 0;
}

/* 抽屉标签：选中的那张从柜体里抽出来，探进内容区 */
.drawer {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 9px var(--s4) 9px var(--s3);
  border-radius: var(--radius) 0 0 var(--radius);
  color: var(--cabinet-ink-2);
  text-decoration: none;
  transition: background-color var(--dur-fast) var(--ease),
    color var(--dur-fast) var(--ease);
}

.drawer__label {
  font-size: var(--fs-base);
  font-weight: 500;
  letter-spacing: 0.01em;
}

.drawer__hint {
  font-size: 10.5px;
  color: inherit;
  opacity: 0.72;
}

.drawer:hover {
  background: var(--cabinet-2);
  color: var(--cabinet-ink);
}

.drawer--open {
  background: var(--paper);
  color: var(--ink);
  margin-right: -1px;
  padding-right: calc(var(--s4) + 1px);
}

.drawer--open .drawer__hint {
  color: var(--ink-3);
  opacity: 1;
}

.rail__foot {
  margin-top: auto;
  padding: var(--s4) var(--s4) 0 0;
  border-top: 1px solid var(--cabinet-3);
}

.rail__footLabel {
  color: var(--cabinet-ink-2);
}

.rail__footValue {
  margin-top: var(--s1);
  font-size: var(--fs-sm);
  color: var(--cabinet-ink);
  word-break: break-word;
}

.rail__footWarn {
  margin-top: var(--s2);
  font-size: var(--fs-xs);
  line-height: 1.5;
  color: #e3c184;
}

@media (max-width: 900px) {
  .rail {
    position: static;
    height: auto;
    gap: var(--s3);
    padding: var(--s3) var(--s4);
  }

  .rail__brand {
    padding-right: 0;
  }

  .rail__sub {
    display: none;
  }

  .rail__nav {
    flex-direction: row;
    flex-wrap: nowrap;
    gap: var(--s1);
    overflow-x: auto;
    padding-bottom: 2px;
  }

  .drawer {
    flex: none;
    border-radius: var(--radius);
    padding: 6px 10px;
  }

  .drawer__hint {
    display: none;
  }

  .drawer--open {
    margin-right: 0;
    padding-right: 10px;
  }

  .rail__foot {
    display: none;
  }
}
</style>
