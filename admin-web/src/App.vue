<template>
  <div v-if="!token" class="login-page">
    <t-card class="login-card" :bordered="false">
      <div class="brand-row">
        <div class="brand-mark">乡</div>
        <div>
          <div class="brand-title">家乡小店管理台</div>
          <div class="brand-sub">商品、订单、快递代收配送统一管理</div>
        </div>
      </div>
      <t-alert
        theme="info"
        message="默认账号 admin，默认密码 admin123456。上线前请通过环境变量修改。"
        style="margin-bottom: 18px"
      />
      <t-form :data="loginForm" label-width="64px" @submit="login">
        <t-form-item label="账号" name="username">
          <t-input v-model="loginForm.username" clearable />
        </t-form-item>
        <t-form-item label="密码" name="password">
          <t-input v-model="loginForm.password" type="password" clearable />
        </t-form-item>
        <t-form-item label="API" name="apiBase">
          <t-input v-model="apiBase" clearable />
        </t-form-item>
        <t-form-item>
          <t-button theme="primary" type="submit" block :loading="loading.login">登录</t-button>
        </t-form-item>
      </t-form>
    </t-card>
  </div>

  <t-layout v-else class="app-shell">
    <t-aside width="232px" class="side">
      <div class="brand-row">
        <div class="brand-mark">乡</div>
        <div>
          <div class="brand-title">家乡小店</div>
          <div class="brand-sub">管理台</div>
        </div>
      </div>
      <t-menu v-model="activeView" theme="light" :collapsed="false">
        <t-menu-item value="dashboard">仪表盘</t-menu-item>
        <t-menu-item value="products">商品管理</t-menu-item>
        <t-menu-item value="orders">订单配送</t-menu-item>
        <t-menu-item value="parcels">快递代收</t-menu-item>
      </t-menu>
    </t-aside>
    <t-layout>
      <t-header class="topbar">
        <div>
          <div class="topbar-title">{{ viewTitle }}</div>
          <div class="brand-sub">{{ apiBase }}</div>
        </div>
        <t-space>
          <t-button variant="outline" @click="refreshAll">刷新</t-button>
          <t-button theme="default" @click="logout">退出</t-button>
        </t-space>
      </t-header>
      <t-content class="workspace">
        <section v-show="activeView === 'dashboard'">
          <div class="section-head">
            <div>
              <h2>经营概览</h2>
              <p>今日处理商品、订单和快递时先看这里</p>
            </div>
          </div>
          <div class="metric-grid">
            <t-card>
              <t-statistic title="商品总数" :value="summary.productCount" />
            </t-card>
            <t-card>
              <t-statistic title="上架商品" :value="summary.onSaleCount" />
            </t-card>
            <t-card>
              <t-statistic title="待处理订单" :value="summary.pendingOrderCount" />
            </t-card>
            <t-card>
              <t-statistic title="待送快递" :value="summary.pendingParcelCount" />
            </t-card>
          </div>
          <t-card title="营业额">
            <t-statistic :value="yuan(summary.revenueCents)" prefix="￥" />
          </t-card>
        </section>

        <section v-show="activeView === 'products'">
          <div class="section-head">
            <div>
              <h2>商品管理</h2>
              <p>维护商品、价格、库存和上下架状态</p>
            </div>
            <t-button theme="primary" @click="openProductDialog()">新增商品</t-button>
          </div>
          <t-card class="table-card" :bordered="false">
            <t-table row-key="id" :data="products" :columns="productColumns" :loading="loading.products">
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
                <t-tag :theme="row.status === 'on_sale' ? 'success' : 'danger'">
                  {{ productStatusLabels[row.status] }}
                </t-tag>
              </template>
              <template #actions="{ row }">
                <t-space>
                  <t-button size="small" variant="text" @click="openProductDialog(row)">编辑</t-button>
                  <t-button size="small" variant="text" @click="toggleProduct(row)">
                    {{ row.status === 'on_sale' ? '下架' : '上架' }}
                  </t-button>
                </t-space>
              </template>
            </t-table>
          </t-card>
        </section>

        <section v-show="activeView === 'orders'">
          <div class="section-head">
            <div>
              <h2>订单配送</h2>
              <p>确认订单、安排配送、完成或取消订单</p>
            </div>
          </div>
          <t-card class="table-card" :bordered="false">
            <t-table row-key="id" :data="orders" :columns="orderColumns" :loading="loading.orders">
              <template #orderNo="{ row }">
                <div class="cell-title">{{ row.orderNo }}</div>
                <div class="cell-sub">{{ formatTime(row.createdAt) }}</div>
              </template>
              <template #receiver="{ row }">
                <div class="cell-title">{{ row.receiverName }} {{ row.receiverPhone }}</div>
                <div class="cell-sub">{{ row.address }}</div>
                <div class="cell-sub">{{ row.note }}</div>
              </template>
              <template #items="{ row }">
                <div class="items-list">
                  <span v-for="item in row.items" :key="item.productId">{{ item.name }} x {{ item.quantity }}</span>
                </div>
              </template>
              <template #totalCents="{ row }">￥{{ yuan(row.totalCents) }}</template>
              <template #status="{ row }">
                <t-tag :theme="orderTheme(row.status)">{{ orderStatusLabels[row.status] }}</t-tag>
              </template>
              <template #actions="{ row }">
                <t-space>
                  <t-select v-model="row.nextStatus" style="width: 118px" size="small">
                    <t-option v-for="item in orderStatusOptions" :key="item.value" :value="item.value" :label="item.label" />
                  </t-select>
                  <t-button size="small" @click="updateOrderStatus(row)">保存</t-button>
                </t-space>
              </template>
            </t-table>
          </t-card>
        </section>

        <section v-show="activeView === 'parcels'">
          <div class="section-head">
            <div>
              <h2>快递代收</h2>
              <p>登记快递并跟随商品订单一起配送</p>
            </div>
            <t-button theme="primary" @click="openParcelDialog">登记快递</t-button>
          </div>
          <t-card class="table-card" :bordered="false">
            <t-table row-key="id" :data="parcels" :columns="parcelColumns" :loading="loading.parcels">
              <template #parcelNo="{ row }">
                <div class="cell-title">{{ row.parcelNo }}</div>
                <div class="cell-sub">{{ row.carrier }} {{ row.pickupCode }}</div>
                <div class="cell-sub">{{ row.trackingNo }}</div>
              </template>
              <template #receiver="{ row }">
                <div class="cell-title">{{ row.receiverName }} {{ row.receiverPhone }}</div>
                <div class="cell-sub">{{ row.address }}</div>
              </template>
              <template #status="{ row }">
                <t-tag :theme="parcelTheme(row.status)">{{ parcelStatusLabels[row.status] }}</t-tag>
              </template>
              <template #actions="{ row }">
                <t-space>
                  <t-select v-model="row.nextStatus" style="width: 112px" size="small">
                    <t-option v-for="item in parcelStatusOptions" :key="item.value" :value="item.value" :label="item.label" />
                  </t-select>
                  <t-button size="small" @click="updateParcelStatus(row)">保存</t-button>
                </t-space>
              </template>
            </t-table>
          </t-card>
        </section>
      </t-content>
    </t-layout>
  </t-layout>

  <t-dialog v-model:visible="productDialogVisible" :header="editingProductId ? '编辑商品' : '新增商品'" width="720px" :footer="false">
    <t-form :data="productForm" label-width="88px" @submit="submitProduct">
      <div class="form-grid">
        <t-form-item label="商品名称" name="name">
          <t-input v-model="productForm.name" />
        </t-form-item>
        <t-form-item label="分类" name="category">
          <t-input v-model="productForm.category" />
        </t-form-item>
        <t-form-item label="售价" name="priceYuan">
          <t-input-number v-model="productForm.priceYuan" theme="normal" :min="0.01" :decimal-places="2" suffix="元" />
        </t-form-item>
        <t-form-item label="库存" name="stock">
          <t-input-number v-model="productForm.stock" theme="normal" :min="0" />
        </t-form-item>
        <t-form-item label="单位" name="unit">
          <t-input v-model="productForm.unit" />
        </t-form-item>
        <t-form-item label="状态" name="status">
          <t-select v-model="productForm.status">
            <t-option value="on_sale" label="上架" />
            <t-option value="off_shelf" label="下架" />
          </t-select>
        </t-form-item>
        <t-form-item class="wide" label="图片地址" name="imageUrl">
          <t-input v-model="productForm.imageUrl" />
        </t-form-item>
        <t-form-item class="wide" label="商品说明" name="description">
          <t-textarea v-model="productForm.description" />
        </t-form-item>
      </div>
      <div class="dialog-footer">
        <t-button theme="default" @click="productDialogVisible = false">取消</t-button>
        <t-button theme="primary" type="submit" :loading="loading.submitProduct">保存</t-button>
      </div>
    </t-form>
  </t-dialog>

  <t-dialog v-model:visible="parcelDialogVisible" header="登记快递" width="720px" :footer="false">
    <t-form :data="parcelForm" label-width="88px" @submit="submitParcel">
      <div class="form-grid">
        <t-form-item label="收件人" name="receiverName">
          <t-input v-model="parcelForm.receiverName" />
        </t-form-item>
        <t-form-item label="手机号" name="receiverPhone">
          <t-input v-model="parcelForm.receiverPhone" />
        </t-form-item>
        <t-form-item label="快递公司" name="carrier">
          <t-input v-model="parcelForm.carrier" />
        </t-form-item>
        <t-form-item label="取件码" name="pickupCode">
          <t-input v-model="parcelForm.pickupCode" />
        </t-form-item>
        <t-form-item class="wide" label="运单号" name="trackingNo">
          <t-input v-model="parcelForm.trackingNo" />
        </t-form-item>
        <t-form-item class="wide" label="配送地址" name="address">
          <t-input v-model="parcelForm.address" />
        </t-form-item>
        <t-form-item class="wide" label="备注" name="note">
          <t-textarea v-model="parcelForm.note" />
        </t-form-item>
      </div>
      <div class="dialog-footer">
        <t-button theme="default" @click="parcelDialogVisible = false">取消</t-button>
        <t-button theme="primary" type="submit" :loading="loading.submitParcel">保存</t-button>
      </div>
    </t-form>
  </t-dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { MessagePlugin } from "tdesign-vue-next";

const defaultApiBase = import.meta.env.VITE_API_BASE || "http://119.45.182.166:3784";
const apiBase = ref(localStorage.getItem("homeShopApiBase") || defaultApiBase);
const token = ref(localStorage.getItem("homeShopAdminToken") || "");
const activeView = ref("dashboard");

const loginForm = reactive({
  username: "admin",
  password: "admin123456"
});

const summary = reactive({
  productCount: 0,
  onSaleCount: 0,
  pendingOrderCount: 0,
  pendingParcelCount: 0,
  revenueCents: 0
});

const loading = reactive({
  login: false,
  products: false,
  orders: false,
  parcels: false,
  submitProduct: false,
  submitParcel: false
});

const products = ref([]);
const orders = ref([]);
const parcels = ref([]);
const productDialogVisible = ref(false);
const parcelDialogVisible = ref(false);
const editingProductId = ref("");

const productForm = reactive(emptyProduct());
const parcelForm = reactive(emptyParcel());

const productStatusLabels = {
  on_sale: "上架",
  off_shelf: "下架"
};

const orderStatusLabels = {
  pending: "待确认",
  confirmed: "待配送",
  delivering: "配送中",
  completed: "已完成",
  cancelled: "已取消"
};

const parcelStatusLabels = {
  pending: "待配送",
  delivering: "配送中",
  completed: "已送达",
  cancelled: "已取消"
};

const orderStatusOptions = Object.entries(orderStatusLabels).map(([value, label]) => ({ value, label }));
const parcelStatusOptions = Object.entries(parcelStatusLabels).map(([value, label]) => ({ value, label }));

const productColumns = [
  { colKey: "name", title: "商品", width: 320 },
  { colKey: "category", title: "分类", width: 110 },
  { colKey: "priceCents", title: "售价", width: 100 },
  { colKey: "stock", title: "库存", width: 100 },
  { colKey: "status", title: "状态", width: 90 },
  { colKey: "actions", title: "操作", width: 150 }
];

const orderColumns = [
  { colKey: "orderNo", title: "订单", width: 160 },
  { colKey: "customerName", title: "下单人", width: 140 },
  { colKey: "receiver", title: "收货老人", width: 280 },
  { colKey: "items", title: "商品", width: 220 },
  { colKey: "totalCents", title: "金额", width: 100 },
  { colKey: "status", title: "状态", width: 100 },
  { colKey: "actions", title: "更新", width: 210 }
];

const parcelColumns = [
  { colKey: "parcelNo", title: "快递", width: 220 },
  { colKey: "receiver", title: "收件人", width: 280 },
  { colKey: "note", title: "备注", width: 220 },
  { colKey: "status", title: "状态", width: 100 },
  { colKey: "actions", title: "更新", width: 210 }
];

const viewTitle = computed(() => ({
  dashboard: "经营概览",
  products: "商品管理",
  orders: "订单配送",
  parcels: "快递代收"
}[activeView.value]));

function emptyProduct() {
  return {
    name: "",
    category: "",
    priceYuan: 0,
    stock: 0,
    unit: "",
    imageUrl: "",
    description: "",
    status: "on_sale"
  };
}

function emptyParcel() {
  return {
    receiverName: "",
    receiverPhone: "",
    carrier: "",
    trackingNo: "",
    pickupCode: "",
    address: "",
    note: ""
  };
}

function yuan(cents) {
  return (Number(cents || 0) / 100).toFixed(2);
}

function formatTime(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

async function request(path, options = {}) {
  const response = await fetch(`${apiBase.value}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token.value ? { Authorization: `Bearer ${token.value}` } : {}),
      ...(options.headers || {})
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) logout(false);
    throw new Error(payload.error || "请求失败");
  }
  return payload.data ?? payload;
}

async function login() {
  loading.login = true;
  try {
    localStorage.setItem("homeShopApiBase", apiBase.value.replace(/\/$/, ""));
    apiBase.value = apiBase.value.replace(/\/$/, "");
    const data = await request("/api/admin/login", {
      method: "POST",
      body: JSON.stringify(loginForm)
    });
    token.value = data.token;
    localStorage.setItem("homeShopAdminToken", token.value);
    await refreshAll();
    MessagePlugin.success("登录成功");
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    loading.login = false;
  }
}

function logout(showMessage = true) {
  token.value = "";
  localStorage.removeItem("homeShopAdminToken");
  if (showMessage) MessagePlugin.success("已退出");
}

async function refreshAll() {
  await Promise.all([loadSummary(), loadProducts(), loadOrders(), loadParcels()]);
}

async function loadSummary() {
  const data = await request("/api/admin/summary");
  Object.assign(summary, data);
}

async function loadProducts() {
  loading.products = true;
  try {
    products.value = await request("/api/admin/products");
  } finally {
    loading.products = false;
  }
}

async function loadOrders() {
  loading.orders = true;
  try {
    const data = await request("/api/admin/orders");
    orders.value = data.map(order => ({ ...order, nextStatus: order.status }));
  } finally {
    loading.orders = false;
  }
}

async function loadParcels() {
  loading.parcels = true;
  try {
    const data = await request("/api/admin/parcels");
    parcels.value = data.map(parcel => ({ ...parcel, nextStatus: parcel.status }));
  } finally {
    loading.parcels = false;
  }
}

function resetReactive(target, source) {
  Object.keys(target).forEach(key => delete target[key]);
  Object.assign(target, source);
}

function openProductDialog(row) {
  editingProductId.value = row?.id || "";
  resetReactive(productForm, row
    ? { ...row, priceYuan: Number(yuan(row.priceCents)) }
    : emptyProduct());
  productDialogVisible.value = true;
}

async function submitProduct() {
  loading.submitProduct = true;
  try {
    const payload = {
      name: productForm.name,
      category: productForm.category,
      priceCents: Math.round(Number(productForm.priceYuan) * 100),
      stock: Number(productForm.stock),
      unit: productForm.unit,
      imageUrl: productForm.imageUrl,
      description: productForm.description,
      status: productForm.status
    };
    await request(editingProductId.value ? `/api/admin/products/${editingProductId.value}` : "/api/admin/products", {
      method: editingProductId.value ? "PUT" : "POST",
      body: JSON.stringify(payload)
    });
    productDialogVisible.value = false;
    await Promise.all([loadProducts(), loadSummary()]);
    MessagePlugin.success("商品已保存");
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    loading.submitProduct = false;
  }
}

async function toggleProduct(row) {
  const nextStatus = row.status === "on_sale" ? "off_shelf" : "on_sale";
  await request(`/api/admin/products/${row.id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status: nextStatus })
  });
  await Promise.all([loadProducts(), loadSummary()]);
}

async function updateOrderStatus(row) {
  await request(`/api/admin/orders/${row.id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status: row.nextStatus })
  });
  await Promise.all([loadOrders(), loadProducts(), loadSummary()]);
  MessagePlugin.success("订单状态已更新");
}

function openParcelDialog() {
  resetReactive(parcelForm, emptyParcel());
  parcelDialogVisible.value = true;
}

async function submitParcel() {
  loading.submitParcel = true;
  try {
    await request("/api/admin/parcels", {
      method: "POST",
      body: JSON.stringify(parcelForm)
    });
    parcelDialogVisible.value = false;
    await Promise.all([loadParcels(), loadSummary()]);
    MessagePlugin.success("快递已登记");
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    loading.submitParcel = false;
  }
}

async function updateParcelStatus(row) {
  await request(`/api/admin/parcels/${row.id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status: row.nextStatus })
  });
  await Promise.all([loadParcels(), loadSummary()]);
  MessagePlugin.success("快递状态已更新");
}

function orderTheme(status) {
  if (status === "completed") return "success";
  if (status === "cancelled") return "danger";
  if (status === "delivering") return "primary";
  return "warning";
}

function parcelTheme(status) {
  if (status === "completed") return "success";
  if (status === "cancelled") return "danger";
  if (status === "delivering") return "primary";
  return "warning";
}

onMounted(() => {
  if (token.value) {
    refreshAll().catch(error => MessagePlugin.error(error.message));
  }
});
</script>
