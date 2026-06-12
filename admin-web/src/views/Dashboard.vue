<template>
  <div>
    <div class="section-head">
      <div>
        <h2>经营概览</h2>
        <p>今日处理商品、订单和快递时先看这里</p>
      </div>
    </div>
    <t-loading :loading="loading" size="large">
      <div class="metric-grid">
        <StatCard label="商品总数" :value="summary.productCount" />
        <StatCard label="上架商品" :value="summary.onSaleCount" />
        <StatCard label="待处理订单" :value="summary.pendingOrderCount" />
        <StatCard label="待送快递" :value="summary.pendingParcelCount" />
      </div>
      <div class="metric-grid" style="grid-template-columns: repeat(2, minmax(180px, 1fr))">
        <div class="card">
          <div class="stat-label">营业额</div>
          <div class="stat-value">
            <span class="stat-unit">￥</span>{{ yuan(summary.revenueCents) }}
          </div>
        </div>
        <StatCard label="今日订单" :value="summary.todayOrderCount" />
      </div>
    </t-loading>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from "vue";
import { request, yuan } from "../utils/api";
import { MessagePlugin } from "tdesign-vue-next";
import StatCard from "../components/StatCard.vue";

const loading = ref(false);
const summary = reactive({
  productCount: 0,
  onSaleCount: 0,
  pendingOrderCount: 0,
  pendingParcelCount: 0,
  revenueCents: 0,
  todayOrderCount: 0
});

onMounted(async () => {
  loading.value = true;
  try {
    const data = await request("/api/admin/summary");
    Object.assign(summary, data);
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    loading.value = false;
  }
});
</script>
