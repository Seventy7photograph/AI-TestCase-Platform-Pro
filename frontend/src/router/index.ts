import { createRouter, createWebHistory } from "vue-router";

import CapabilityView from "@/views/CapabilityView.vue";
import DocumentsView from "@/views/DocumentsView.vue";
import RequirementView from "@/views/RequirementView.vue";
import SuiteDetailView from "@/views/SuiteDetailView.vue";
import SuitesView from "@/views/SuitesView.vue";
import WorkbenchView from "@/views/WorkbenchView.vue";

export const router = createRouter({
  history: createWebHistory("/"),
  routes: [
    {
      path: "/",
      name: "workbench",
      component: WorkbenchView,
      meta: { nav: "workbench", title: "工作台" },
    },
    {
      path: "/documents",
      name: "documents",
      component: DocumentsView,
      meta: { nav: "documents", title: "文档库" },
    },
    {
      path: "/documents/:docId/requirement",
      name: "requirement",
      component: RequirementView,
      meta: { nav: "documents", title: "结构化需求" },
    },
    {
      path: "/suites",
      name: "suites",
      component: SuitesView,
      meta: { nav: "suites", title: "用例集" },
    },
    {
      path: "/suites/:suiteId",
      name: "suite-detail",
      component: SuiteDetailView,
      meta: { nav: "suites", title: "用例集详情" },
    },
    {
      path: "/capability",
      name: "capability",
      component: CapabilityView,
      meta: { nav: "capability", title: "运行状态" },
    },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
  scrollBehavior: () => ({ top: 0 }),
});
