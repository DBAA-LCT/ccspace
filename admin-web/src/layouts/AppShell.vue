<template>
  <t-layout class="app-shell">
    <t-aside width="240px" class="side">
      <div class="brand-row">
        <div class="brand-mark">乡</div>
        <div>
          <div class="brand-title">家乡小店</div>
          <div class="brand-sub">管理台</div>
        </div>
      </div>
      <nav class="side-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="side-link"
          :class="{ active: $route.path === item.path }"
        >
          {{ item.label }}
        </router-link>
      </nav>
    </t-aside>
    <t-layout>
      <t-header class="topbar">
        <div>
          <div class="topbar-title">{{ currentLabel }}</div>
          <div class="topbar-sub">{{ apiBase }}</div>
        </div>
        <t-space>
          <t-button variant="outline" size="small" @click="refreshAll">刷新</t-button>
          <t-button size="small" @click="logout">退出</t-button>
        </t-space>
      </t-header>
      <t-content class="workspace">
        <router-view />
      </t-content>
    </t-layout>
  </t-layout>
</template>

<script setup>
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { apiBase, clearToken } from "../utils/api";
import { MessagePlugin } from "tdesign-vue-next";

const router = useRouter();
const route = useRoute();

const navItems = [
  { path: "/", label: "仪表盘" },
  { path: "/products", label: "商品管理" },
  { path: "/orders", label: "订单配送" },
  { path: "/parcels", label: "快递代收" }
];

const currentLabel = computed(() => {
  const item = navItems.find(n => n.path === route.path);
  return item?.label || "家乡小店";
});

function logout() {
  clearToken();
  router.push("/login");
  MessagePlugin.success("已退出");
}

function refreshAll() {
  window.location.reload();
}
</script>
