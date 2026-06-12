<template>
  <t-layout class="app-shell">
    <t-aside :width="collapsed ? '64px' : '240px'" class="side" :class="{ collapsed }">
      <div class="brand-row" @click="router.push('/')">
        <div class="brand-mark">CC</div>
        <div v-if="!collapsed" class="brand-info">
          <div class="brand-title">CCspace</div>
          <div class="brand-sub">管理台</div>
        </div>
      </div>
      <nav class="side-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="side-link"
          :class="{ active: isActive(item.path) }"
          :title="item.label"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="side-footer">
        <div class="side-link" @click="collapsed = !collapsed" :title="collapsed ? '展开' : '收起'">
          <span class="nav-icon">{{ collapsed ? '→' : '←' }}</span>
          <span v-if="!collapsed" class="nav-label">收起菜单</span>
        </div>
      </div>
    </t-aside>
    <t-layout>
      <t-header class="topbar">
        <div class="topbar-left">
          <t-button class="mobile-menu-btn" variant="text" size="small" @click="collapsed = !collapsed">☰</t-button>
          <div>
            <div class="topbar-title">{{ currentLabel }}</div>
          </div>
        </div>
        <t-space>
          <t-button variant="outline" size="small" @click="refreshData">刷新</t-button>
          <t-button size="small" @click="logout">退出</t-button>
        </t-space>
      </t-header>
      <t-content class="workspace">
        <router-view :key="route.fullPath" />
      </t-content>
    </t-layout>
  </t-layout>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { clearToken } from "../utils/api";
import { MessagePlugin } from "tdesign-vue-next";

const router = useRouter();
const route = useRoute();
const collapsed = ref(false);

const navItems = [
  { path: "/", icon: "📊", label: "仪表盘" },
  { path: "/products", icon: "📦", label: "商品管理" },
  { path: "/orders", icon: "📋", label: "订单配送" },
  { path: "/parcels", icon: "🚚", label: "快递代收" },
  { path: "/delivery-plan", icon: "🗺️", label: "配送排单" },
  { path: "/promotions", icon: "🏷️", label: "促销活动" },
  { path: "/admins", icon: "👤", label: "管理员" },
  { path: "/preview", icon: "📱", label: "小程序预览" }
];

const currentLabel = computed(() => {
  const item = navItems.find(n => {
    if (n.path === "/") return route.path === "/";
    return route.path.startsWith(n.path);
  });
  return item?.label || "CCspace";
});

function isActive(path) {
  if (path === "/") return route.path === "/";
  return route.path.startsWith(path);
}

function logout() {
  clearToken();
  router.push("/login");
  MessagePlugin.success("已退出");
}

function refreshData() {
  router.replace({ path: route.path, query: { ...route.query, _t: Date.now() } });
}
</script>
