<template>
  <div>
    <div class="section-head">
      <div>
        <h2>订单配送</h2>
        <p>确认订单、安排配送、完成或取消订单</p>
      </div>
    </div>

    <div class="filter-bar">
      <t-input v-model="searchQ" placeholder="搜索订单号、姓名、手机号..." clearable style="width: 280px" @enter="load(1)" />
      <t-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 120px" @change="load(1)">
        <t-option v-for="item in orderStatusOptions" :key="item.value" :value="item.value" :label="item.label" />
      </t-select>
    </div>

    <div class="table-card">
      <t-table row-key="id" :data="orders" :columns="orderColumns" :loading="loading" bordered>
        <template #orderNo="{ row }">
          <div class="cell-title mono">{{ row.orderNo }}</div>
          <div class="cell-sub">{{ formatTime(row.createdAt) }}</div>
          <div class="cell-sub" v-if="row.deliveryDate">期望送达: {{ row.deliveryDate }}</div>
        </template>
        <template #customer="{ row }">
          <div class="cell-title">{{ row.customerName }}</div>
          <div class="cell-sub">{{ row.customerPhone }}</div>
        </template>
        <template #receiver="{ row }">
          <div class="cell-title">{{ row.receiverName }} {{ row.receiverPhone }}</div>
          <div class="cell-sub">{{ row.address }}</div>
          <div class="cell-sub" v-if="row.note">备注: {{ row.note }}</div>
          <div class="cell-sub" v-if="row.deliveryType">
            <span class="badge badge-info">{{ deliveryTypeLabels[row.deliveryType] || row.deliveryType }}</span>
          </div>
        </template>
        <template #items="{ row }">
          <div class="items-list">
            <span v-for="item in row.items" :key="item.productId">{{ item.name }} x {{ item.quantity }}</span>
          </div>
        </template>
        <template #totalCents="{ row }">
          <span style="font-weight: 500">￥{{ yuan(row.totalCents) }}</span>
          <div v-if="row.discountCents > 0" class="cell-sub" style="color: #ee0000">-￥{{ yuan(row.discountCents) }}</div>
        </template>
        <template #status="{ row }">
          <span class="badge" :class="badgeClass(row.status)">{{ orderStatusLabels[row.status] }}</span>
          <div v-if="row.deliveryPhoto" class="cell-sub" style="margin-top: 4px">
            <img :src="row.deliveryPhoto" class="photo-thumb" @click="previewPhoto(row.deliveryPhoto)" />
          </div>
        </template>
        <template #actions="{ row }">
          <t-space direction="vertical" :size="4">
            <t-space v-if="row.status !== 'completed' && row.status !== 'cancelled'">
              <t-select v-model="row.nextStatus" style="width: 110px" size="small">
                <t-option v-for="item in getNextStatusOptions(row.status)" :key="item.value" :value="item.value" :label="item.label" />
              </t-select>
              <t-button size="small" theme="primary" @click="updateStatus(row)">保存</t-button>
            </t-space>
            <t-button v-if="row.status === 'delivering' && !row.deliveryPhoto" size="small" variant="outline" @click="openPhotoDialog(row)">上传送达照片</t-button>
          </t-space>
        </template>
      </t-table>
      <div class="table-footer" v-if="total > pageSize">
        <t-pagination v-model="page" :total="total" :page-size="pageSize" @change="load" show-jumper />
      </div>
    </div>

    <t-dialog v-model:visible="photoDialogVisible" header="上传送达照片" width="min(480px, 90vw)" :footer="false">
      <t-form :data="photoForm" label-width="80px" @submit="uploadPhoto">
        <t-form-item label="照片URL" name="photoUrl">
          <t-input v-model="photoForm.photoUrl" placeholder="输入图片地址或上传后的URL" />
        </t-form-item>
        <div class="dialog-footer">
          <t-button theme="default" @click="photoDialogVisible = false">取消</t-button>
          <t-button theme="primary" type="submit" :loading="photoSubmitting" shape="round">确认</t-button>
        </div>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { request, yuan, formatTime } from "../utils/api";
import { orderStatusLabels, orderStatusOptions, orderTheme, deliveryTypeLabels, statusBadgeClass } from "../utils/constants";
import { MessagePlugin, DialogPlugin } from "tdesign-vue-next";

const orders = ref([]);
const loading = ref(false);
const searchQ = ref("");
const filterStatus = ref("");
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);
const photoDialogVisible = ref(false);
const photoSubmitting = ref(false);
const photoTargetId = ref("");
const photoForm = reactive({ photoUrl: "" });

const VALID_ORDER_TRANSITIONS = {
  pending: ["confirmed", "cancelled"],
  confirmed: ["delivering", "cancelled"],
  delivering: ["completed", "cancelled"],
  completed: [],
  cancelled: []
};

function getNextStatusOptions(currentStatus) {
  const valid = VALID_ORDER_TRANSITIONS[currentStatus] || [];
  return orderStatusOptions.filter(opt => valid.includes(opt.value));
}

function badgeClass(status) {
  return statusBadgeClass(status, orderTheme);
}

function previewPhoto(url) {
  window.open(url, "_blank");
}

function openPhotoDialog(row) {
  photoTargetId.value = row.id;
  photoForm.photoUrl = "";
  photoDialogVisible.value = true;
}

async function uploadPhoto() {
  if (!photoForm.photoUrl) return;
  photoSubmitting.value = true;
  try {
    await request(`/api/admin/orders/${photoTargetId.value}/delivery-photo`, {
      method: "PATCH",
      body: JSON.stringify({ photoUrl: photoForm.photoUrl })
    });
    photoDialogVisible.value = false;
    await load();
    MessagePlugin.success("送达照片已上传");
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    photoSubmitting.value = false;
  }
}

async function load(p) {
  if (p) page.value = p;
  loading.value = true;
  try {
    const params = new URLSearchParams({ page: page.value, page_size: pageSize.value });
    if (searchQ.value) params.set("q", searchQ.value);
    if (filterStatus.value) params.set("status", filterStatus.value);
    const result = await request(`/api/admin/orders?${params}`);
    if (Array.isArray(result)) {
      orders.value = result.map(o => ({ ...o, nextStatus: o.status }));
      total.value = result.length;
    } else {
      orders.value = (result.data || result).map(o => ({ ...o, nextStatus: o.status }));
      total.value = result.total ?? orders.value.length;
    }
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    loading.value = false;
  }
}

async function updateStatus(row) {
  const label = orderStatusLabels[row.nextStatus] || row.nextStatus;
  const confirm = DialogPlugin.confirm({
    header: "确认变更",
    body: `确定将订单 ${row.orderNo} 状态变更为「${label}」吗？`,
    onConfirm: async () => {
      try {
        await request(`/api/admin/orders/${row.id}/status`, {
          method: "PATCH",
          body: JSON.stringify({ status: row.nextStatus })
        });
        await load();
        MessagePlugin.success("订单状态已更新");
      } catch (error) {
        MessagePlugin.error(error.message);
      }
      confirm.hide();
    },
    onClose: () => confirm.hide()
  });
}

onMounted(load);
</script>

<style scoped>
.photo-thumb {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  object-fit: cover;
  cursor: pointer;
  border: 1px solid var(--hairline);
}
</style>
