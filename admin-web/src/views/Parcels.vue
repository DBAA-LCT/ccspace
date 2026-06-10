<template>
  <div>
    <div class="section-head">
      <div>
        <h2>快递代收</h2>
        <p>登记快递并跟随商品订单一起配送</p>
      </div>
      <t-button theme="primary" shape="round" @click="openDialog">登记快递</t-button>
    </div>
    <div class="table-card">
      <t-table row-key="id" :data="parcels" :columns="parcelColumns" :loading="loading" bordered>
        <template #parcelNo="{ row }">
          <div class="cell-title" style="font-family: 'JetBrains Mono', monospace; font-size: 13px">{{ row.parcelNo }}</div>
          <div class="cell-sub">{{ row.carrier }} {{ row.pickupCode }}</div>
          <div class="cell-sub" v-if="row.trackingNo">{{ row.trackingNo }}</div>
        </template>
        <template #receiver="{ row }">
          <div class="cell-title">{{ row.receiverName }} {{ row.receiverPhone }}</div>
          <div class="cell-sub">{{ row.address }}</div>
        </template>
        <template #status="{ row }">
          <span class="badge" :class="badgeClass(row.status)">{{ parcelStatusLabels[row.status] }}</span>
        </template>
        <template #actions="{ row }">
          <t-space>
            <t-select v-model="row.nextStatus" style="width: 110px" size="small">
              <t-option v-for="item in parcelStatusOptions" :key="item.value" :value="item.value" :label="item.label" />
            </t-select>
            <t-button size="small" theme="primary" @click="updateStatus(row)">保存</t-button>
          </t-space>
        </template>
      </t-table>
    </div>

    <t-dialog v-model:visible="dialogVisible" header="登记快递" width="680px" :footer="false">
      <t-form :data="form" label-width="80px" @submit="submit">
        <div class="form-grid">
          <t-form-item label="收件人" name="receiverName">
            <t-input v-model="form.receiverName" />
          </t-form-item>
          <t-form-item label="手机号" name="receiverPhone">
            <t-input v-model="form.receiverPhone" />
          </t-form-item>
          <t-form-item label="快递公司" name="carrier">
            <t-input v-model="form.carrier" />
          </t-form-item>
          <t-form-item label="取件码" name="pickupCode">
            <t-input v-model="form.pickupCode" />
          </t-form-item>
          <t-form-item class="wide" label="运单号" name="trackingNo">
            <t-input v-model="form.trackingNo" />
          </t-form-item>
          <t-form-item class="wide" label="配送地址" name="address">
            <t-input v-model="form.address" />
          </t-form-item>
          <t-form-item class="wide" label="备注" name="note">
            <t-textarea v-model="form.note" />
          </t-form-item>
        </div>
        <div class="dialog-footer">
          <t-button theme="default" @click="dialogVisible = false">取消</t-button>
          <t-button theme="primary" type="submit" :loading="submitting" shape="round">登记</t-button>
        </div>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { request } from "../utils/api";
import { parcelStatusLabels, parcelStatusOptions, parcelTheme } from "../utils/constants";
import { MessagePlugin } from "tdesign-vue-next";

const parcels = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const submitting = ref(false);

function emptyForm() {
  return { receiverName: "", receiverPhone: "", carrier: "", trackingNo: "", pickupCode: "", address: "", note: "" };
}
const form = reactive(emptyForm());

function badgeClass(status) {
  const theme = parcelTheme(status);
  return { success: "badge-success", danger: "badge-error", primary: "badge-info", warning: "badge-warning" }[theme] || "badge-warning";
}

async function load() {
  loading.value = true;
  try {
    const data = await request("/api/admin/parcels");
    parcels.value = data.map(p => ({ ...p, nextStatus: p.status }));
  } finally {
    loading.value = false;
  }
}

function openDialog() {
  Object.keys(form).forEach(k => delete form[k]);
  Object.assign(form, emptyForm());
  dialogVisible.value = true;
}

async function submit() {
  submitting.value = true;
  try {
    await request("/api/admin/parcels", { method: "POST", body: JSON.stringify(form) });
    dialogVisible.value = false;
    await load();
    MessagePlugin.success("快递已登记");
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    submitting.value = false;
  }
}

async function updateStatus(row) {
  await request(`/api/admin/parcels/${row.id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status: row.nextStatus })
  });
  await load();
  MessagePlugin.success("快递状态已更新");
}

onMounted(load);
</script>
