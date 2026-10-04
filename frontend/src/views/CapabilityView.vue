<script setup lang="ts">
import { computed, onMounted } from "vue";

import { notice } from "@/composables/useNotice";
import { useHealthStore } from "@/stores/health";
import ErrorNote from "@/components/ErrorNote.vue";
import PageHead from "@/components/PageHead.vue";
import StatStrip from "@/components/StatStrip.vue";
import type { StatItem } from "@/components/StatStrip.vue";

const health = useHealthStore();

const info = computed(() => health.info);

const V1_ORDER = ["equivalence", "boundary", "scenario"];

const orderedMethods = computed(() => {
  const list = info.value?.methods ?? [];
  return [...list].sort((a, b) => {
    const indexA = V1_ORDER.indexOf(a.name);
    const indexB = V1_ORDER.indexOf(b.name);
    if (indexA !== -1 || indexB !== -1) {
      if (indexA === -1) return 1;
      if (indexB === -1) return -1;
      return indexA - indexB;
    }
    return a.name.localeCompare(b.name);
  });
});

const statItems = computed<StatItem[]>(() => {
  const current = info.value;
  if (!current) return [];
  const implemented = current.methods.filter((method) => method.implemented).length;
  return [
    { label: "服务", value: current.app_name, hint: "后端 FastAPI 应用标识", mono: false },
    { label: "版本", value: `v${current.version}`, hint: "接口与模型版本" },
    {
      label: "状态",
      value: current.status === "ok" ? "正常" : current.status,
      tone: current.status === "ok" ? "good" : "warn",
      hint: "健康检查 /api/v1/health 的返回",
    },
    {
      label: "推理引擎",
      value: current.llm_available ? current.llm_provider : "规则引擎",
      tone: current.llm_available ? "good" : "warn",
      hint: current.llm_available
        ? `${current.llm_model || "未指定模型"}`
        : current.llm_degraded_reason || "未配置 API Key，链路自动降级",
    },
    {
      label: "设计方法",
      value: `${implemented} / ${current.methods.length}`,
      hint: "已实现的方法数 / 已注册的方法数",
    },
  ];
});

onMounted(() => {
  void health.load(true);
});

async function refresh(): Promise<void> {
  await health.load(true);
  if (health.reachable) {
    notice.success("已重新检测服务状态。");
  } else if (health.error) {
    notice.error(health.error);
  }
}
</script>

<template>
  <div class="stack">
    <PageHead
      title="运行状态"
      note="当前服务的真实能力边界。已注册但未实现的能力会明确标注，避免误以为可用。"
    >
      <template #actions>
        <el-button title="重新请求 /api/v1/health，刷新能力清单" @click="refresh">
          重新检测
        </el-button>
      </template>
    </PageHead>

    <ErrorNote v-if="health.error" :error="new Error(health.error)" />

    <el-skeleton v-if="health.loading && !info" :rows="5" animated class="pad" />

    <template v-else-if="info">
      <StatStrip :items="statItems" />

      <div class="grid grid--2">
        <section class="card">
          <div class="card__head"><span class="card__title">测试设计方法</span></div>
          <ul class="list">
            <li v-for="method in orderedMethods" :key="method.name" class="list__row">
              <span class="list__key">
                <span class="mono list__code">{{ method.name }}</span>
                <span class="list__label">{{ method.label }}</span>
              </span>
              <span
                class="state"
                :class="method.implemented ? 'state--on' : 'state--off'"
                :title="
                  method.implemented
                    ? '当前版本已实现，可直接调用'
                    : '已注册但未实现，调用会返回 501'
                "
              >
                {{ method.implemented ? "已实现" : "调用返回 501" }}
              </span>
            </li>
          </ul>
        </section>

        <section class="card">
          <div class="card__head"><span class="card__title">导出格式</span></div>
          <ul class="list">
            <li v-for="format in info.export_formats" :key="format.name" class="list__row">
              <span class="list__key">
                <span class="mono list__code">.{{ format.extension }}</span>
                <span class="list__label">{{ format.label }}</span>
              </span>
              <span class="mono dim list__media">{{ format.media_type }}</span>
            </li>
          </ul>
        </section>

        <section class="card">
          <div class="card__head"><span class="card__title">支持的上传格式</span></div>
          <div class="card__body seealso">
            <span v-for="ext in info.supported_extensions" :key="ext" class="chip mono">
              {{ ext }}
            </span>
          </div>
        </section>

        <section class="card">
          <div class="card__head"><span class="card__title">外部集成</span></div>
          <ul v-if="health.integrations.length" class="list">
            <li v-for="item in health.integrations" :key="item.name" class="list__row">
              <span class="list__key">
                <span class="mono list__code">{{ item.name }}</span>
                <span class="list__label">{{ item.label }}</span>
              </span>
              <span
                class="state"
                :class="item.implemented ? 'state--on' : 'state--off'"
                :title="item.implemented ? '当前版本已实现' : '计划在 V3.0 提供'"
              >
                {{ item.implemented ? "已实现" : "V3 预留" }}
              </span>
            </li>
          </ul>
          <div v-else class="card__body dim">未注册任何外部集成。</div>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.pad {
  padding: var(--s5);
}

.list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.list__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s3);
  padding: var(--s3) var(--s4);
}

.list__row + .list__row {
  border-top: 1px solid var(--rule);
}

.list__key {
  display: flex;
  align-items: baseline;
  gap: var(--s2);
  min-width: 0;
}

.list__code {
  font-size: var(--fs-xs);
  color: var(--ink-3);
}

.list__label {
  font-size: var(--fs-base);
  color: var(--ink);
}

.list__media {
  font-size: var(--fs-xs);
}

.state {
  flex: none;
  font-size: var(--fs-xs);
  border-radius: var(--radius-sm);
  padding: 1px 7px;
  border: 1px solid transparent;
}

.state--on {
  color: var(--ok);
  background: var(--ok-wash);
  border-color: rgba(44, 106, 76, 0.3);
}

.state--off {
  color: var(--ink-3);
  background: var(--paper-sunk);
  border-color: var(--rule-strong);
}

.chip {
  font-size: var(--fs-xs);
  color: var(--ink-2);
  border: 1px solid var(--rule-strong);
  border-radius: var(--radius-sm);
  padding: 1px 6px;
}
</style>
