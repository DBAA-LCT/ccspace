<template>
  <div>
    <div class="section-head">
      <div>
        <h2>经营概览</h2>
        <p>今日处理商品、订单和快递时先看这里</p>
      </div>
    </div>
    <div class="metric-grid">
      <StatCard label="商品总数" :value="summary.productCount" />
      <StatCard label="上架商品" :value="summary.onSaleCount" />
      <StatCard label="待处理订单" :value="summary.pendingOrderCount" />
      <StatCard label="待送快递" :value="summary.pendingParcelCount" />
    </div>
    <div class="card" style="max-width: 320px">
      <div class="stat-label">营业额</div>
      <div class="stat-value">
        <span class="stat-unit">￥</span>{{ yuan(summary.revenueCents) }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted } from "vue";
import { request, yuan } from "../utils/api";
import { MessagePlugin } from "tdesign-vue-next";
import StatCard from "../components/StatCard.vue";

const summary = reactive({
  productCount: 0,
  onSaleCount: 0,
  pendingOrderCount: 0,
  pendingParcelCount: 0,
  revenueCents: 0
});

onMounted(async () => {
  try {
    const data = await request("/api/admin/summary");
    Object.assign(summary, data);
  } catch (error) {
    MessagePlugin.error(error.message);
  }
});
</script>
