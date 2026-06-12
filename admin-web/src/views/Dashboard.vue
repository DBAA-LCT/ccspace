<template>
  <div>
    <div class="section-head">
      <div>
        <h2>经营概览</h2>
        <p>今日处理商品、订单和快递时先看这里</p>
      </div>
    </div>

    <div class="filter-bar"></div>

    <t-loading :loading="loading" size="large">
      <div class="table-card" style="padding: var(--sp-lg)">
        <div class="metric-grid">
          <div class="card stat-card stat-blue">
            <div class="stat-label">商品总数</div>
            <div class="stat-value">{{ summary.productCount }}</div>
          </div>
          <div class="card stat-card stat-green">
            <div class="stat-label">上架商品</div>
            <div class="stat-value">{{ summary.onSaleCount }}</div>
          </div>
          <div class="card stat-card stat-orange">
            <div class="stat-label">待处理订单</div>
            <div class="stat-value">{{ summary.pendingOrderCount }}</div>
          </div>
          <div class="card stat-card stat-purple">
            <div class="stat-label">待送快递</div>
            <div class="stat-value">{{ summary.pendingParcelCount }}</div>
          </div>
        </div>
        <div class="metric-grid" style="grid-template-columns: repeat(2, minmax(180px, 1fr))">
          <div class="card stat-card stat-red">
            <div class="stat-label">营业额</div>
            <div class="stat-value">
              <span class="stat-unit">￥</span>{{ yuan(summary.revenueCents) }}
            </div>
          </div>
          <div class="card stat-card stat-cyan">
            <div class="stat-label">今日订单</div>
            <div class="stat-value">{{ summary.todayOrderCount }}</div>
          </div>
        </div>
      </div>
    </t-loading>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from "vue";
import { request, yuan } from "../utils/api";
import { MessagePlugin } from "tdesign-vue-next";

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
