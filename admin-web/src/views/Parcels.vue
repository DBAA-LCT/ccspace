<template>
  <div>
    <div class="section-head">
      <div>
        <h2>快递代收</h2>
        <p>登记快递并跟随商品订单一起配送</p>
      </div>
      <t-button theme="primary" shape="round" @click="openDialog">登记快递</t-button>
    </div>

    <div class="filter-bar">
      <t-input v-model="searchQ" placeholder="搜索收件人、手机号、运单号..." clearable style="width: 280px" @enter="load(1)" />
      <t-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 120px" @change="load(1)">
        <t-option v-for="item in parcelStatusOptions" :key="item.value" :value="item.value" :label="item.label" />
      </t-select>
    </div>

    <div class="table-card">
      <t-table row-key="id" :data="parcels" :columns="parcelColumns" :loading="loading" bordered>
        <template #parcelNo="{ row }">
          <div class="cell-title mono">{{ row.parcelNo }}</div>
          <div class="cell-sub">{{ row.carrier }} · 取件码: {{ row.pickupCode }}</div>
          <div class="cell-sub" v-if="row.trackingNo">运单: {{ row.trackingNo }}</div>
        </template>
        <template #receiver="{ row }">
          <div class="cell-title">{{ row.receiverName }} {{ row.receiverPhone }}</div>
          <div class="cell-sub">{{ row.address }}</div>
        </template>
        <template #note="{ row }">
          <div class="cell-sub">{{ row.note || '—' }}</div>
        </template>
        <template #status="{ row }">
          <span class="badge" :class="badgeClass(row.status)">{{ parcelStatusLabels[row.status] }}</span>
        </template>
        <template #actions="{ row }">
          <t-space v-if="row.status !== 'completed' && row.status !== 'cancelled'">
            <t-select v-model="row.nextStatus" style="width: 110px" size="small">
              <t-option v-for="item in getNextStatusOptions(row.status)" :key="item.value" :value="item.value" :label="item.label" />
            </t-select>
            <t-button size="small" theme="primary" @click="updateStatus(row)">保存</t-button>
          </t-space>
          <span v-else class="cell-sub">—</span>
        </template>
      </t-table>
      <div class="table-footer" v-if="total > pageSize">
        <t-pagination v-model="page" :total="total" :page-size="pageSize" @change="load" show-jumper />
      </div>
    </div>

    <t-dialog v-model:visible="dialogVisible" header="登记快递" width="min(680px, 90vw)" :footer="false">
      <t-form :data="form" label-width="80px" :rules="formRules" @submit="submit">
        <div class="form-grid">
          <t-form-item label="收件人" name="receiverName">
            <t-input v-model="form.receiverName" placeholder="收件人姓名" />
          </t-form-item>
          <t-form-item label="手机号" name="receiverPhone">
            <t-input v-model="form.receiverPhone" placeholder="11位手机号" />
          </t-form-item>
          <t-form-item label="快递公司" name="carrier">
            <t-input v-model="form.carrier" placeholder="如：中通快递" />
          </t-form-item>
          <t-form-item label="取件码" name="pickupCode">
            <t-input v-model="form.pickupCode" placeholder="驿站取件码" />
          </t-form-item>
          <t-form-item class="wide" label="运单号" name="trackingNo">
            <t-input v-model="form.trackingNo" placeholder="可选" />
          </t-form-item>
          <t-form-item class="wide" label="配送地址" name="address">
            <t-input v-model="form.address" placeholder="配送到哪里" />
          </t-form-item>
          <t-form-item class="wide" label="备注" name="note">
            <t-textarea v-model="form.note" placeholder="可选备注" />
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
import { parcelStatusLabels, parcelStatusOptions, parcelTheme, statusBadgeClass } from "../utils/constants";
import { MessagePlugin, DialogPlugin } from "tdesign-vue-next";

const parcels = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const submitting = ref(false);
const searchQ = ref("");
const filterStatus = ref("");
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);

const VALID_PARCEL_TRANSITIONS = {
  pending: ["delivering", "cancelled"],
  delivering: ["completed", "cancelled"],
  completed: [],
  cancelled: []
};

function getNextStatusOptions(currentStatus) {
  const valid = VALID_PARCEL_TRANSITIONS[currentStatus] || [];
  return parcelStatusOptions.filter(opt => valid.includes(opt.value));
}

function emptyForm() {
  return { receiverName: "", receiverPhone: "", carrier: "", trackingNo: "", pickupCode: "", address: "", note: "" };
}
const form = reactive(emptyForm());

const formRules = {
  receiverName: [{ required: true, message: "请输入收件人姓名" }],
  receiverPhone: [{ required: true, message: "请输入手机号" }],
  carrier: [{ required: true, message: "请输入快递公司" }],
  pickupCode: [{ required: true, message: "请输入取件码" }],
  address: [{ required: true, message: "请输入配送地址" }]
};

function badgeClass(status) {
  return statusBadgeClass(status, parcelTheme);
}

async function load(p) {
  if (p) page.value = p;
  loading.value = true;
  try {
    const params = new URLSearchParams({ page: page.value, page_size: pageSize.value });
    if (searchQ.value) params.set("q", searchQ.value);
    if (filterStatus.value) params.set("status", filterStatus.value);
    const result = await request(`/api/admin/parcels?${params}`);
    if (Array.isArray(result)) {
      parcels.value = result.map(p => ({ ...p, nextStatus: p.status }));
      total.value = result.length;
    } else {
      parcels.value = (result.data || result).map(p => ({ ...p, nextStatus: p.status }));
      total.value = result.total ?? parcels.value.length;
    }
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    loading.value = false;
  }
}

function openDialog() {
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
  const label = parcelStatusLabels[row.nextStatus] || row.nextStatus;
  const confirm = DialogPlugin.confirm({
    header: "确认变更",
    body: `确定将快递 ${row.parcelNo} 状态变更为「${label}」吗？`,
    onConfirm: async () => {
      try {
        await request(`/api/admin/parcels/${row.id}/status`, {
          method: "PATCH",
          body: JSON.stringify({ status: row.nextStatus })
        });
        await load();
        MessagePlugin.success("快递状态已更新");
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
