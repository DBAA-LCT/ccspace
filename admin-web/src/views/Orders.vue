<template>
  <div>
    <div class="section-head">
      <div>
        <h2>订单配送</h2>
        <p>确认订单、安排配送、完成或取消订单</p>
      </div>
    </div>
    <div class="table-card">
      <t-table row-key="id" :data="orders" :columns="orderColumns" :loading="loading" bordered>
        <template #orderNo="{ row }">
          <div class="cell-title" style="font-family: 'JetBrains Mono', monospace; font-size: 13px">{{ row.orderNo }}</div>
          <div class="cell-sub">{{ formatTime(row.createdAt) }}</div>
        </template>
        <template #receiver="{ row }">
          <div class="cell-title">{{ row.receiverName }} {{ row.receiverPhone }}</div>
          <div class="cell-sub">{{ row.address }}</div>
          <div class="cell-sub" v-if="row.note">{{ row.note }}</div>
        </template>
        <template #items="{ row }">
          <div class="items-list">
            <span v-for="item in row.items" :key="item.productId">{{ item.name }} x {{ item.quantity }}</span>
          </div>
        </template>
        <template #totalCents="{ row }">
          <span style="font-weight: 500">￥{{ yuan(row.totalCents) }}</span>
        </template>
        <template #status="{ row }">
          <span class="badge" :class="badgeClass(row.status)">{{ orderStatusLabels[row.status] }}</span>
        </template>
        <template #actions="{ row }">
          <t-space>
            <t-select v-model="row.nextStatus" style="width: 110px" size="small">
              <t-option v-for="item in orderStatusOptions" :key="item.value" :value="item.value" :label="item.label" />
            </t-select>
            <t-button size="small" theme="primary" @click="updateStatus(row)">保存</t-button>
          </t-space>
        </template>
      </t-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { request, yuan, formatTime } from "../utils/api";
import { orderStatusLabels, orderStatusOptions, orderTheme } from "../utils/constants";
import { MessagePlugin } from "tdesign-vue-next";

const orders = ref([]);
const loading = ref(false);

function badgeClass(status) {
  const theme = orderTheme(status);
  return { success: "badge-success", danger: "badge-error", primary: "badge-info", warning: "badge-warning" }[theme] || "badge-warning";
}

async function load() {
  loading.value = true;
  try {
    const data = await request("/api/admin/orders");
    orders.value = data.map(o => ({ ...o, nextStatus: o.status }));
  } finally {
    loading.value = false;
  }
}

async function updateStatus(row) {
  await request(`/api/admin/orders/${row.id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status: row.nextStatus })
  });
  await load();
  MessagePlugin.success("订单状态已更新");
}

onMounted(load);
</script>
