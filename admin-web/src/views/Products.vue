<template>
  <div>
    <div class="section-head">
      <div>
        <h2>商品管理</h2>
        <p>维护商品、价格、库存和上下架状态</p>
      </div>
      <t-button theme="primary" shape="round" @click="openDialog()">新增商品</t-button>
    </div>
    <div class="table-card">
      <t-table row-key="id" :data="products" :columns="productColumns" :loading="loading" bordered>
        <template #name="{ row }">
          <div class="product-cell">
            <img :src="row.imageUrl" alt="" />
            <div>
              <div class="cell-title">{{ row.name }}</div>
              <div class="cell-sub">{{ row.description || '暂无说明' }}</div>
            </div>
          </div>
        </template>
        <template #priceCents="{ row }">￥{{ yuan(row.priceCents) }}</template>
        <template #stock="{ row }">{{ row.stock }} {{ row.unit }}</template>
        <template #status="{ row }">
          <span class="badge" :class="row.status === 'on_sale' ? 'badge-success' : 'badge-error'">
            {{ productStatusLabels[row.status] }}
          </span>
        </template>
        <template #actions="{ row }">
          <t-space>
            <t-button size="small" variant="text" @click="openDialog(row)">编辑</t-button>
            <t-button size="small" variant="text" theme="danger" @click="toggle(row)">
              {{ row.status === 'on_sale' ? '下架' : '上架' }}
            </t-button>
          </t-space>
        </template>
      </t-table>
    </div>

    <t-dialog v-model:visible="dialogVisible" :header="editingId ? '编辑商品' : '新增商品'" width="680px" :footer="false">
      <t-form :data="form" label-width="80px" @submit="submit">
        <div class="form-grid">
          <t-form-item label="名称" name="name">
            <t-input v-model="form.name" />
          </t-form-item>
          <t-form-item label="分类" name="category">
            <t-input v-model="form.category" />
          </t-form-item>
          <t-form-item label="售价" name="priceYuan">
            <t-input-number v-model="form.priceYuan" theme="normal" :min="0.01" :decimal-places="2" suffix="元" />
          </t-form-item>
          <t-form-item label="库存" name="stock">
            <t-input-number v-model="form.stock" theme="normal" :min="0" />
          </t-form-item>
          <t-form-item label="单位" name="unit">
            <t-input v-model="form.unit" />
          </t-form-item>
          <t-form-item label="状态" name="status">
            <t-select v-model="form.status">
              <t-option value="on_sale" label="上架" />
              <t-option value="off_shelf" label="下架" />
            </t-select>
          </t-form-item>
          <t-form-item class="wide" label="图片地址" name="imageUrl">
            <t-input v-model="form.imageUrl" />
          </t-form-item>
          <t-form-item class="wide" label="说明" name="description">
            <t-textarea v-model="form.description" />
          </t-form-item>
        </div>
        <div class="dialog-footer">
          <t-button theme="default" @click="dialogVisible = false">取消</t-button>
          <t-button theme="primary" type="submit" :loading="submitting" shape="round">保存</t-button>
        </div>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { request, yuan } from "../utils/api";
import { productStatusLabels, productColumns } from "../utils/constants";
import { MessagePlugin } from "tdesign-vue-next";

const products = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const editingId = ref("");
const submitting = ref(false);

function emptyForm() {
  return { name: "", category: "", priceYuan: 0, stock: 0, unit: "", imageUrl: "", description: "", status: "on_sale" };
}
const form = reactive(emptyForm());

async function load() {
  loading.value = true;
  try {
    products.value = await request("/api/admin/products");
  } finally {
    loading.value = false;
  }
}

function openDialog(row) {
  editingId.value = row?.id || "";
  Object.keys(form).forEach(k => delete form[k]);
  Object.assign(form, row ? { ...row, priceYuan: Number(yuan(row.priceCents)) } : emptyForm());
  dialogVisible.value = true;
}

async function submit() {
  submitting.value = true;
  try {
    const payload = { ...form, priceCents: Math.round(Number(form.priceYuan) * 100), stock: Number(form.stock) };
    delete payload.priceYuan;
    await request(editingId.value ? `/api/admin/products/${editingId.value}` : "/api/admin/products", {
      method: editingId.value ? "PUT" : "POST",
      body: JSON.stringify(payload)
    });
    dialogVisible.value = false;
    await load();
    MessagePlugin.success("商品已保存");
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    submitting.value = false;
  }
}

async function toggle(row) {
  await request(`/api/admin/products/${row.id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status: row.status === "on_sale" ? "off_shelf" : "on_sale" })
  });
  await load();
}

onMounted(load);
</script>
