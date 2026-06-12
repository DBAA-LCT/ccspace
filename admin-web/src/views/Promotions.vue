<template>
  <div>
    <div class="section-head">
      <div>
        <h2>促销活动</h2>
        <p>管理限时特价和满减优惠</p>
      </div>
      <t-button theme="primary" shape="round" @click="openDialog()">新建促销</t-button>
    </div>

    <div class="table-card">
      <t-table row-key="id" :data="promotions" :columns="promoColumns" :loading="loading" bordered>
        <template #type="{ row }">
          <span class="badge" :class="row.type === 'direct' ? 'badge-success' : 'badge-info'">
            {{ row.type === 'direct' ? '限时特价' : '满减' }}
          </span>
        </template>
        <template #discount="{ row }">
          <span style="color: #ee0000; font-weight: 500">-￥{{ yuan(row.discountCents) }}</span>
          <span v-if="row.thresholdCents > 0" class="cell-sub">满{{ yuan(row.thresholdCents) }}可用</span>
        </template>
        <template #isActive="{ row }">
          <span class="badge" :class="row.isActive ? 'badge-success' : 'badge-error'">
            {{ row.isActive ? '生效中' : '已停用' }}
          </span>
        </template>
        <template #period="{ row }">
          <div class="cell-sub">{{ formatTime(row.startAt) }}</div>
          <div class="cell-sub">至 {{ formatTime(row.endAt) }}</div>
        </template>
        <template #actions="{ row }">
          <t-button size="small" variant="text" @click="toggleActive(row)">
            {{ row.isActive ? '停用' : '启用' }}
          </t-button>
        </template>
      </t-table>
    </div>

    <t-dialog v-model:visible="dialogVisible" header="新建促销" width="min(520px, 90vw)" :footer="false">
      <t-form :data="form" label-width="100px" @submit="submit">
        <t-form-item label="活动名称" name="name">
          <t-input v-model="form.name" placeholder="如：牛奶限时特价" />
        </t-form-item>
        <t-form-item label="类型" name="type">
          <t-select v-model="form.type">
            <t-option value="direct" label="限时特价（商品直降）" />
            <t-option value="full_reduction" label="满减（满额立减）" />
          </t-select>
        </t-form-item>
        <t-form-item label="满减门槛" name="thresholdCents" v-if="form.type === 'full_reduction'">
          <t-input-number v-model="form.thresholdYuan" theme="normal" :min="0.01" :decimal-places="2" suffix="元" />
        </t-form-item>
        <t-form-item label="优惠金额" name="discountYuan">
          <t-input-number v-model="form.discountYuan" theme="normal" :min="0.01" :decimal-places="2" suffix="元" />
        </t-form-item>
        <t-form-item label="关联商品" name="productId" v-if="form.type === 'direct'">
          <t-input v-model="form.productId" placeholder="输入商品ID（可选）" />
        </t-form-item>
        <t-form-item label="开始时间" name="startAt">
          <t-input v-model="form.startAt" placeholder="YYYY-MM-DDTHH:MM:SS" />
        </t-form-item>
        <t-form-item label="结束时间" name="endAt">
          <t-input v-model="form.endAt" placeholder="YYYY-MM-DDTHH:MM:SS" />
        </t-form-item>
        <div class="dialog-footer">
          <t-button theme="default" @click="dialogVisible = false">取消</t-button>
          <t-button theme="primary" type="submit" :loading="submitting" shape="round">创建</t-button>
        </div>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { request, yuan, formatTime } from "../utils/api";
import { MessagePlugin } from "tdesign-vue-next";

const promotions = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const submitting = ref(false);

const promoColumns = [
  { colKey: "name", title: "活动", minWidth: 160 },
  { colKey: "type", title: "类型", width: 100 },
  { colKey: "discount", title: "优惠", width: 130 },
  { colKey: "isActive", title: "状态", width: 90 },
  { colKey: "period", title: "有效期", width: 200 },
  { colKey: "actions", title: "操作", width: 100 }
];

function emptyForm() {
  return {
    name: "", type: "direct", thresholdYuan: 0, discountYuan: 0,
    productId: "", startAt: "", endAt: ""
  };
}
const form = reactive(emptyForm());

async function load() {
  loading.value = true;
  try {
    promotions.value = await request("/api/admin/promotions");
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    loading.value = false;
  }
}

function openDialog() {
  Object.assign(form, emptyForm());
  const now = new Date();
  form.startAt = now.toISOString().slice(0, 19);
  const weekLater = new Date(now.getTime() + 7 * 86400000);
  form.endAt = weekLater.toISOString().slice(0, 19);
  dialogVisible.value = true;
}

async function submit() {
  submitting.value = true;
  try {
    await request("/api/admin/promotions", {
      method: "POST",
      body: JSON.stringify({
        name: form.name,
        type: form.type,
        thresholdCents: Math.round(form.thresholdYuan * 100),
        discountCents: Math.round(form.discountYuan * 100),
        productId: form.productId ? Number(form.productId) : null,
        startAt: form.startAt,
        endAt: form.endAt
      })
    });
    dialogVisible.value = false;
    await load();
    MessagePlugin.success("促销已创建");
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    submitting.value = false;
  }
}

async function toggleActive(row) {
  try {
    await request(`/api/admin/promotions/${row.id}`, {
      method: "PATCH",
      body: JSON.stringify({ isActive: !row.isActive })
    });
    await load();
    MessagePlugin.success(row.isActive ? "已停用" : "已启用");
  } catch (error) {
    MessagePlugin.error(error.message);
  }
}

onMounted(load);
</script>
