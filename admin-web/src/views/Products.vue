<template>
  <div>
    <div class="section-head">
      <div>
        <h2>商品管理</h2>
        <p>维护商品、价格、库存和上下架状态</p>
      </div>
      <t-button theme="primary" shape="round" @click="openDialog()">新增商品</t-button>
    </div>

    <div class="filter-bar">
      <t-input v-model="searchQ" placeholder="搜索商品名称..." clearable style="width: 220px" @enter="load(1)" />
      <t-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 120px" @change="load(1)">
        <t-option value="on_sale" label="上架" />
        <t-option value="off_shelf" label="下架" />
      </t-select>
      <t-select v-model="filterCategory" placeholder="分类筛选" clearable style="width: 140px" @change="load(1)">
        <t-option v-for="c in categories" :key="c" :value="c" :label="c" />
      </t-select>
    </div>

    <div class="table-card">
      <t-table row-key="id" :data="products" :columns="productColumns" :loading="loading" bordered>
        <template #name="{ row }">
          <div class="product-cell">
            <img :src="row.imageUrl" :alt="row.name" />
            <div>
              <div class="cell-title">{{ row.name }}</div>
              <div class="cell-sub">{{ row.description || '暂无说明' }}</div>
            </div>
          </div>
        </template>
        <template #category="{ row }">
          <span class="cell-sub">{{ row.category }}</span>
        </template>
        <template #priceCents="{ row }">￥{{ yuan(row.priceCents) }}</template>
        <template #stock="{ row }">
          <span :class="{ 'stock-low': row.stock <= 3 }">{{ row.stock }} {{ row.unit }}</span>
        </template>
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
      <div class="table-footer" v-if="total > pageSize">
        <t-pagination v-model="page" :total="total" :page-size="pageSize" @change="load" show-jumper />
      </div>
    </div>

    <t-dialog v-model:visible="dialogVisible" :header="editingId ? '编辑商品' : '新增商品'" width="min(680px, 90vw)" :footer="false">
      <t-form :data="form" label-width="80px" :rules="formRules" @submit="submit">
        <div class="form-grid">
          <t-form-item label="名称" name="name">
            <t-input v-model="form.name" placeholder="请输入商品名称" />
          </t-form-item>
          <t-form-item label="分类" name="category">
            <t-input v-model="form.category" placeholder="如：粮油副食" />
          </t-form-item>
          <t-form-item label="售价" name="priceYuan">
            <t-input-number v-model="form.priceYuan" theme="normal" :min="0.01" :decimal-places="2" suffix="元" />
          </t-form-item>
          <t-form-item label="原价" name="originalPriceYuan">
            <t-input-number v-model="form.originalPriceYuan" theme="normal" :min="0" :decimal-places="2" suffix="元（留空表示无折扣）" />
          </t-form-item>
          <t-form-item label="库存" name="stock">
            <t-input-number v-model="form.stock" theme="normal" :min="0" />
          </t-form-item>
          <t-form-item label="单位" name="unit">
            <t-input v-model="form.unit" placeholder="如：袋、箱、提" />
          </t-form-item>
          <t-form-item label="状态" name="status">
            <t-select v-model="form.status">
              <t-option value="on_sale" label="上架" />
              <t-option value="off_shelf" label="下架" />
            </t-select>
          </t-form-item>
          <t-form-item class="wide" label="图片地址" name="imageUrl">
            <t-input v-model="form.imageUrl" placeholder="https://..." />
          </t-form-item>
          <t-form-item class="wide" label="图片预览" v-if="form.imageUrl">
            <img :src="form.imageUrl" class="image-preview" @error="imgErr = true" v-show="!imgErr" />
            <span v-show="imgErr" class="cell-sub">图片加载失败</span>
          </t-form-item>
          <t-form-item class="wide" label="说明" name="description">
            <t-textarea v-model="form.description" placeholder="商品描述" />
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
import { ref, reactive, onMounted, watch } from "vue";
import { request, yuan } from "../utils/api";
import { productStatusLabels, productColumns } from "../utils/constants";
import { MessagePlugin, DialogPlugin } from "tdesign-vue-next";

const products = ref([]);
const categories = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const editingId = ref("");
const submitting = ref(false);
const imgErr = ref(false);

const searchQ = ref("");
const filterStatus = ref("");
const filterCategory = ref("");
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);

function emptyForm() {
  return { name: "", category: "", priceYuan: 0, originalPriceYuan: 0, stock: 0, unit: "", imageUrl: "", description: "", status: "on_sale" };
}
const form = reactive(emptyForm());

const formRules = {
  name: [{ required: true, message: "请输入商品名称" }],
  category: [{ required: true, message: "请输入分类" }],
  priceYuan: [{ required: true, message: "请输入售价" }],
  unit: [{ required: true, message: "请输入单位" }]
};

watch(dialogVisible, (val) => {
  if (!val) imgErr.value = false;
});

async function load(p) {
  if (p) page.value = p;
  loading.value = true;
  try {
    const params = new URLSearchParams({ page: page.value, page_size: pageSize.value });
    if (searchQ.value) params.set("q", searchQ.value);
    if (filterStatus.value) params.set("status", filterStatus.value);
    if (filterCategory.value) params.set("category", filterCategory.value);
    const result = await request(`/api/admin/products?${params}`);
    if (Array.isArray(result)) {
      products.value = result;
      total.value = result.length;
    } else {
      products.value = result.data || result;
      total.value = result.total ?? products.value.length;
    }
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    loading.value = false;
  }
}

async function loadCategories() {
  try {
    const data = await request("/api/products/categories");
    categories.value = data || [];
  } catch { /* ignore */ }
}

function openDialog(row) {
  editingId.value = row?.id || "";
  Object.assign(form, row ? {
    ...row,
    priceYuan: Number(yuan(row.priceCents)),
    originalPriceYuan: row.originalPriceCents ? Number(yuan(row.originalPriceCents)) : 0
  } : emptyForm());
  dialogVisible.value = true;
}

async function submit() {
  submitting.value = true;
  try {
    const payload = {
      ...form,
      priceCents: Math.round(Number(form.priceYuan) * 100),
      originalPriceCents: form.originalPriceYuan ? Math.round(Number(form.originalPriceYuan) * 100) : null,
      stock: Number(form.stock)
    };
    delete payload.priceYuan;
    delete payload.originalPriceYuan;
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
  const action = row.status === "on_sale" ? "下架" : "上架";
  const confirm = DialogPlugin.confirm({
    header: `确认${action}`,
    body: `确定要${action}「${row.name}」吗？`,
    onConfirm: async () => {
      try {
        await request(`/api/admin/products/${row.id}/status`, {
          method: "PATCH",
          body: JSON.stringify({ status: row.status === "on_sale" ? "off_shelf" : "on_sale" })
        });
        await load();
        MessagePlugin.success(`已${action}`);
      } catch (error) {
        MessagePlugin.error(error.message);
      }
      confirm.hide();
    },
    onClose: () => confirm.hide()
  });
}

onMounted(() => {
  load();
  loadCategories();
});
</script>
