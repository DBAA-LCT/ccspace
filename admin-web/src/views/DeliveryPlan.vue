<template>
  <div>
    <div class="section-head">
      <div>
        <h2>配送排单</h2>
        <p>按地址分组查看待配送的订单和快递，合理安排配送路线</p>
      </div>
      <t-date-picker v-model="selectedDate" :clearable="true" placeholder="选择日期筛选" @change="load" />
    </div>

    <t-loading :loading="loading" size="large">
      <div v-if="Object.keys(plan.byAddress).length === 0" class="card" style="text-align: center; padding: 48px">
        <t-empty description="暂无待配送的订单和快递" />
      </div>

      <div v-else class="delivery-groups">
        <div v-for="(group, address) in plan.byAddress" :key="address" class="delivery-group card">
          <div class="group-header">
            <h3>📍 {{ address }}</h3>
            <t-space>
              <span class="badge badge-info">{{ group.orders.length }} 个订单</span>
              <span class="badge badge-warning">{{ group.parcels.length }} 个快递</span>
            </t-space>
          </div>

          <div v-if="group.orders.length > 0" class="group-section">
            <div class="group-label">订单</div>
            <div v-for="order in group.orders" :key="order.id" class="group-item">
              <div class="item-main">
                <span class="cell-title mono">{{ order.orderNo }}</span>
                <span class="cell-sub">{{ order.receiverName }} {{ order.receiverPhone }}</span>
                <span class="cell-sub">
                  <span v-for="item in order.items" :key="item.productId" class="item-tag">{{ item.name }}x{{ item.quantity }}</span>
                </span>
                <span class="cell-sub" v-if="order.deliveryDate">期望: {{ order.deliveryDate }}</span>
              </div>
              <div class="item-right">
                <span class="badge" :class="orderBadgeClass(order.status)">{{ orderStatusLabel(order.status) }}</span>
                <span style="font-weight: 500; margin-left: 8px">￥{{ yuan(order.totalCents) }}</span>
              </div>
            </div>
          </div>

          <div v-if="group.parcels.length > 0" class="group-section">
            <div class="group-label">快递</div>
            <div v-for="parcel in group.parcels" :key="parcel.id" class="group-item">
              <div class="item-main">
                <span class="cell-title mono">{{ parcel.parcelNo }}</span>
                <span class="cell-sub">{{ parcel.receiverName }} · {{ parcel.carrier }} · {{ parcel.pickupCode }}</span>
              </div>
              <div class="item-right">
                <span class="badge" :class="parcelBadgeClass(parcel.status)">{{ parcelStatusLabel(parcel.status) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </t-loading>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { request, yuan } from "../utils/api";
import { orderStatusLabels, parcelStatusLabels, orderTheme, parcelTheme, statusBadgeClass } from "../utils/constants";
import { MessagePlugin } from "tdesign-vue-next";

const loading = ref(false);
const selectedDate = ref("");
const plan = reactive({ orders: [], parcels: [], byAddress: {} });

function orderStatusLabel(s) { return orderStatusLabels[s] || s; }
function parcelStatusLabel(s) { return parcelStatusLabels[s] || s; }
function orderBadgeClass(s) { return statusBadgeClass(s, orderTheme); }
function parcelBadgeClass(s) { return statusBadgeClass(s, parcelTheme); }

async function load() {
  loading.value = true;
  try {
    const params = new URLSearchParams();
    if (selectedDate.value) params.set("date", selectedDate.value);
    const data = await request(`/api/admin/delivery-plan?${params}`);
    Object.assign(plan, data);
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.delivery-groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.delivery-group {
  padding: 20px;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--hairline);
}

.group-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.group-section {
  margin-bottom: 12px;
}

.group-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--mute);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  margin-bottom: 8px;
}

.group-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
}

.group-item:last-child {
  border-bottom: none;
}

.item-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.item-tag {
  display: inline-block;
  margin-right: 6px;
  padding: 1px 6px;
  border-radius: 4px;
  background: #f5f5f5;
  font-size: 12px;
}
</style>
