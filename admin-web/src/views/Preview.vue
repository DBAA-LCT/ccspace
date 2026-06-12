<template>
  <div class="preview-page">
    <div class="preview-toolbar">
      <h2>小程序预览</h2>
      <p>实时预览用户在小程序端看到的界面效果</p>
    </div>

    <div class="phone-wrapper">
      <div class="phone">
        <div class="phone-status-bar">
          <span>12:30</span>
          <span class="status-icons">📶 🔋</span>
        </div>
        <div class="phone-nav-bar">
          <span class="nav-title">{{ currentPageTitle }}</span>
        </div>

        <div class="phone-content" ref="contentRef">
          <!-- Home Page -->
          <div v-if="activeTab === 'home'" class="mp-page">
            <div class="mp-hero">
              <div>
                <div class="mp-hero-title">给家人买点需要的</div>
                <div class="mp-hero-sub">下单后由小店送到家</div>
              </div>
              <div class="mp-cart-btn" @click="activeTab = 'cart'">
                购物车 {{ cartCount }}
              </div>
            </div>

            <div class="mp-search">
              <input v-model="searchKey" placeholder="搜索商品..." @keyup.enter="loadProducts" />
            </div>

            <div v-if="loadingProducts" class="mp-loading">加载中...</div>
            <div v-else-if="products.length === 0" class="mp-empty">暂无商品</div>
            <div v-else class="mp-product-list">
              <div v-for="item in products" :key="item.id" class="mp-product-card" @click="viewDetail(item)">
                <img :src="item.imageUrl" :alt="item.name" class="mp-product-img" />
                <div class="mp-product-body">
                  <div class="mp-product-head">
                    <span class="mp-product-name">{{ item.name }}</span>
                    <span class="mp-tag">{{ item.category }}</span>
                  </div>
                  <div class="mp-product-desc">{{ item.description }}</div>
                  <div class="mp-product-foot">
                    <div>
                      <span class="mp-price">￥{{ yuan(item.priceCents) }}</span>
                      <span class="mp-unit"> / {{ item.unit }}</span>
                      <span class="mp-stock" :class="{ 'mp-stock-low': item.stock <= 3 }">
                        {{ item.stock <= 3 ? '仅剩' + item.stock : '库存' + item.stock }}
                      </span>
                    </div>
                    <button class="mp-add-btn" @click.stop="addToCart(item)">加入</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Detail Page -->
          <div v-if="activeTab === 'detail' && selectedProduct" class="mp-page">
            <img :src="selectedProduct.imageUrl" :alt="selectedProduct.name" class="mp-detail-img" />
            <div class="mp-detail-body">
              <div class="mp-detail-head">
                <span class="mp-detail-name">{{ selectedProduct.name }}</span>
                <span class="mp-tag">{{ selectedProduct.category }}</span>
              </div>
              <div class="mp-detail-price">
                <span class="mp-price">￥{{ yuan(selectedProduct.priceCents) }}</span>
                <span class="mp-unit"> / {{ selectedProduct.unit }}</span>
              </div>
              <div class="mp-detail-stock">
                库存: {{ selectedProduct.stock }} {{ selectedProduct.unit }}
                <span v-if="selectedProduct.stock <= 3" style="color: #ee0000; margin-left: 8px">库存紧张</span>
              </div>
              <div class="mp-detail-desc" v-if="selectedProduct.description">
                <div class="mp-desc-label">商品说明</div>
                <div class="mp-desc-text">{{ selectedProduct.description }}</div>
              </div>
            </div>
            <div class="mp-detail-actions">
              <button class="mp-primary-btn" @click="addToCart(selectedProduct)">加入购物车</button>
              <button class="mp-outline-btn" @click="activeTab = 'cart'">购物车 ({{ cartCount }})</button>
            </div>
          </div>

          <!-- Cart Page -->
          <div v-if="activeTab === 'cart'" class="mp-page">
            <div v-if="cart.length === 0" class="mp-empty-block">
              <div class="mp-empty-icon">🛒</div>
              <div class="mp-empty-text">购物车为空</div>
              <button class="mp-primary-btn mp-btn-sm" @click="activeTab = 'home'">去选商品</button>
            </div>
            <div v-else>
              <div class="mp-cart-list">
                <div v-for="item in cart" :key="item.id" class="mp-cart-item">
                  <img :src="item.imageUrl" class="mp-cart-img" />
                  <div class="mp-cart-info">
                    <div class="mp-cart-name">{{ item.name }}</div>
                    <div class="mp-muted">￥{{ yuan(item.priceCents) }} / {{ item.unit }}</div>
                    <div class="mp-cart-qty">
                      <button class="mp-qty-btn" @click="changeQty(item, -1)">-</button>
                      <span class="mp-qty-val">{{ item.quantity }}</span>
                      <button class="mp-qty-btn" @click="changeQty(item, 1)">+</button>
                      <button class="mp-remove-btn" @click="removeFromCart(item)">移除</button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="mp-cart-total">
                <span>合计</span>
                <span class="mp-price mp-price-lg">￥{{ cartTotal }}</span>
              </div>

              <div class="mp-form-section">
                <div class="mp-form-title">订单信息</div>
                <div class="mp-form-field">
                  <label>下单人</label>
                  <input v-model="orderForm.customerName" placeholder="你的姓名" />
                </div>
                <div class="mp-form-field">
                  <label>手机号</label>
                  <input v-model="orderForm.customerPhone" placeholder="用于查询订单" type="tel" />
                </div>
                <div class="mp-form-field">
                  <label>收货人</label>
                  <input v-model="orderForm.receiverName" placeholder="收货人姓名" />
                </div>
                <div class="mp-form-field">
                  <label>联系电话</label>
                  <input v-model="orderForm.receiverPhone" placeholder="收货人电话" type="tel" />
                </div>
                <div class="mp-form-field">
                  <label>配送地址</label>
                  <textarea v-model="orderForm.address" placeholder="村名、组名、门牌或明显地标" rows="2"></textarea>
                </div>
                <div class="mp-form-field">
                  <label>备注</label>
                  <textarea v-model="orderForm.note" placeholder="例如：和快递一起送" rows="2"></textarea>
                </div>
                <button class="mp-primary-btn" @click="submitOrder" :disabled="submitting">
                  {{ submitting ? '提交中...' : '提交订单' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Orders Page -->
          <div v-if="activeTab === 'orders'" class="mp-page">
            <div class="mp-search">
              <input v-model="queryPhone" placeholder="输入手机号查询订单" type="tel" @keyup.enter="loadOrders" />
              <button class="mp-search-btn" @click="loadOrders">查询</button>
            </div>

            <div v-if="loadingOrders" class="mp-loading">加载中...</div>
            <div v-else-if="orders.length === 0 && queryPhone" class="mp-empty">暂无订单</div>
            <div v-else-if="orders.length === 0 && !queryPhone" class="mp-empty">请输入手机号查询订单</div>
            <div v-else class="mp-order-list">
              <div v-for="order in orders" :key="order.id" class="mp-order-card">
                <div class="mp-order-head">
                  <div>
                    <div class="mp-order-no">{{ order.orderNo }}</div>
                    <div class="mp-muted">{{ formatTime(order.createdAt) }}</div>
                  </div>
                  <span class="mp-status" :class="orderStatusClass(order.status)">{{ orderStatusLabel(order.status) }}</span>
                </div>
                <div class="mp-order-receiver">
                  <div class="mp-receiver-name">{{ order.receiverName }} {{ order.receiverPhone }}</div>
                  <div class="mp-muted">{{ order.address }}</div>
                </div>
                <div class="mp-order-items">
                  <div v-for="item in order.items" :key="item.productId" class="mp-order-item-line">
                    {{ item.name }} x {{ item.quantity }}
                  </div>
                </div>
                <div class="mp-order-foot">
                  <div class="mp-muted">{{ order.note }}</div>
                  <div class="mp-price">￥{{ yuan(order.totalCents) }}</div>
                </div>
                <div v-if="order.status === 'pending' || order.status === 'confirmed'" class="mp-order-actions">
                  <button class="mp-outline-btn mp-btn-sm" @click="cancelOrder(order)">取消订单</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Profile Page -->
          <div v-if="activeTab === 'profile'" class="mp-page">
            <div class="mp-profile-form">
              <div class="mp-form-title">我的信息</div>
              <div class="mp-form-field">
                <label>下单人</label>
                <input v-model="profile.customerName" placeholder="你的姓名" />
              </div>
              <div class="mp-form-field">
                <label>手机号</label>
                <input v-model="profile.customerPhone" placeholder="用于查询订单" type="tel" />
              </div>
              <div class="mp-form-field">
                <label>收货人</label>
                <input v-model="profile.receiverName" placeholder="收货人姓名" />
              </div>
              <div class="mp-form-field">
                <label>联系电话</label>
                <input v-model="profile.receiverPhone" placeholder="收货人电话" type="tel" />
              </div>
              <div class="mp-form-field">
                <label>配送地址</label>
                <textarea v-model="profile.address" placeholder="村名、组名、门牌或明显地标" rows="2"></textarea>
              </div>
              <div class="mp-form-field">
                <label>默认备注</label>
                <textarea v-model="profile.note" placeholder="配送偏好等" rows="2"></textarea>
              </div>
              <button class="mp-primary-btn" @click="saveProfile">保存信息</button>
            </div>
            <div class="mp-tip">
              小程序上线前，需要把后端部署到 HTTPS 域名，并在微信公众平台配置 request 合法域名。
            </div>
          </div>
        </div>

        <div class="phone-tab-bar">
          <div
            v-for="tab in tabs"
            :key="tab.key"
            class="tab-item"
            :class="{ active: activeTab === tab.key || (tab.key === 'home' && activeTab === 'detail') }"
            @click="switchTab(tab.key)"
          >
            <span class="tab-icon">{{ tab.icon }}</span>
            <span class="tab-label">{{ tab.label }}</span>
            <span v-if="tab.key === 'cart' && cartCount > 0" class="tab-badge">{{ cartCount }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue";
import { request, yuan, formatTime } from "../utils/api";
import { MessagePlugin } from "tdesign-vue-next";

const activeTab = ref("home");
const selectedProduct = ref(null);
const searchKey = ref("");
const queryPhone = ref("");
const submitting = ref(false);
const loadingProducts = ref(false);
const loadingOrders = ref(false);
const contentRef = ref(null);

const tabs = [
  { key: "home", icon: "🏠", label: "商品" },
  { key: "cart", icon: "🛒", label: "购物车" },
  { key: "orders", icon: "📋", label: "订单" },
  { key: "profile", icon: "👤", label: "我的" }
];

const products = ref([]);
const cart = ref([]);
const orders = ref([]);
const profile = reactive({
  customerName: "",
  customerPhone: "",
  receiverName: "",
  receiverPhone: "",
  address: "",
  note: ""
});
const orderForm = reactive({
  customerName: "",
  customerPhone: "",
  receiverName: "",
  receiverPhone: "",
  address: "",
  note: ""
});

const orderStatusLabels = {
  pending: "待确认", confirmed: "待配送", delivering: "配送中",
  completed: "已完成", cancelled: "已取消"
};

const pageTitles = {
  home: "CCspace", detail: "商品详情", cart: "购物车",
  orders: "订单", profile: "我的"
};

const currentPageTitle = computed(() => pageTitles[activeTab.value] || "CCspace");
const cartCount = computed(() => cart.value.reduce((s, i) => s + i.quantity, 0));
const cartTotal = computed(() => yuan(cart.value.reduce((s, i) => s + i.priceCents * i.quantity, 0)));

function orderStatusLabel(s) { return orderStatusLabels[s] || s; }
function orderStatusClass(s) {
  if (s === "completed") return "mp-status-success";
  if (s === "cancelled") return "mp-status-danger";
  if (s === "delivering") return "mp-status-info";
  return "mp-status-warn";
}

function switchTab(key) {
  activeTab.value = key;
  if (key === "home") { selectedProduct.value = null; loadProducts(); }
  if (key === "orders") loadOrders();
  if (contentRef.value) contentRef.value.scrollTop = 0;
}

function viewDetail(product) {
  selectedProduct.value = product;
  activeTab.value = "detail";
  if (contentRef.value) contentRef.value.scrollTop = 0;
}

function addToCart(product) {
  const existing = cart.value.find(i => i.id === product.id);
  if (existing) {
    if (existing.quantity >= product.stock) { MessagePlugin.warning("库存不够了"); return; }
    existing.quantity++;
  } else {
    cart.value.push({ ...product, quantity: 1 });
  }
  MessagePlugin.success("已加入购物车");
}

function changeQty(item, delta) {
  item.quantity += delta;
  if (item.quantity <= 0) { removeFromCart(item); return; }
  if (item.quantity > item.stock) { item.quantity = item.stock; MessagePlugin.warning("已达库存上限"); }
}

function removeFromCart(item) {
  cart.value = cart.value.filter(i => i.id !== item.id);
}

async function loadProducts() {
  loadingProducts.value = true;
  try {
    let url = "/api/products?status=on_sale";
    if (searchKey.value) url += "&q=" + encodeURIComponent(searchKey.value);
    products.value = await request(url);
  } catch (e) { MessagePlugin.error(e.message); }
  finally { loadingProducts.value = false; }
}

async function loadOrders() {
  if (!queryPhone.value) { orders.value = []; return; }
  loadingOrders.value = true;
  try {
    orders.value = await request(`/api/orders?phone=${encodeURIComponent(queryPhone.value)}`);
  } catch (e) { MessagePlugin.error(e.message); }
  finally { loadingOrders.value = false; }
}

async function submitOrder() {
  const f = orderForm;
  if (!f.customerName || !f.customerPhone || !f.receiverName || !f.receiverPhone || !f.address) {
    MessagePlugin.warning("请补全联系人和地址"); return;
  }
  if (!/^1[3-9]\d{9}$/.test(f.customerPhone)) { MessagePlugin.warning("下单人手机号格式不正确"); return; }
  if (!/^1[3-9]\d{9}$/.test(f.receiverPhone)) { MessagePlugin.warning("收货人电话格式不正确"); return; }
  submitting.value = true;
  try {
    const order = await request("/api/orders", {
      method: "POST",
      data: {
        ...f,
        deliveryType: "home_delivery",
        items: cart.value.map(i => ({ productId: Number(i.id), quantity: i.quantity }))
      }
    });
    Object.assign(profile, f);
    cart.value = [];
    MessagePlugin.success(`下单成功，订单号：${order.orderNo}`);
    activeTab.value = "orders";
    queryPhone.value = f.customerPhone;
    loadOrders();
  } catch (e) { MessagePlugin.error(e.message); }
  finally { submitting.value = false; }
}

function cancelOrder(order) {
  if (!confirm(`确定取消订单 ${order.orderNo}？`)) return;
  request(`/api/orders/${order.id}/cancel`, { method: "PATCH" })
    .then(() => { MessagePlugin.success("已取消"); loadOrders(); })
    .catch(e => MessagePlugin.error(e.message));
}

function saveProfile() {
  Object.assign(orderForm, profile);
  MessagePlugin.success("已保存");
}

onMounted(() => {
  loadProducts();
});
</script>

<style scoped>
.preview-page {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.preview-toolbar {
  width: 100%;
  margin-bottom: 24px;
}

.preview-toolbar h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.6px;
}

.preview-toolbar p {
  margin: 4px 0 0;
  color: #666;
  font-size: 14px;
}

/* ─── Phone Frame ─── */
.phone-wrapper {
  display: flex;
  justify-content: center;
}

.phone {
  width: 375px;
  height: 720px;
  border-radius: 40px;
  border: 8px solid #1a1a1a;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15), 0 2px 8px rgba(0,0,0,0.08);
  position: relative;
}

.phone-status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 44px;
  padding: 0 24px;
  background: #ffffff;
  font-size: 14px;
  font-weight: 600;
  color: #171717;
}

.status-icons { font-size: 12px; }

.phone-nav-bar {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  border-bottom: 1px solid #ebebeb;
  font-size: 17px;
  font-weight: 600;
  color: #171717;
}

/* ─── Content ─── */
.phone-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

.mp-page {
  padding: 16px;
  min-height: 100%;
}

/* ─── Hero ─── */
.mp-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
  background: #ffffff;
  border: 1px solid #ebebeb;
  border-radius: 12px;
  margin-bottom: 12px;
}

.mp-hero-title {
  font-size: 18px;
  font-weight: 600;
  color: #171717;
}

.mp-hero-sub {
  margin-top: 4px;
  color: #666;
  font-size: 13px;
}

.mp-cart-btn {
  flex-shrink: 0;
  padding: 6px 14px;
  border-radius: 20px;
  background: #171717;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

/* ─── Search ─── */
.mp-search {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.mp-search input {
  flex: 1;
  height: 36px;
  border: 1px solid #ebebeb;
  border-radius: 8px;
  padding: 0 12px;
  font-size: 14px;
  outline: none;
  background: #fff;
}

.mp-search input:focus { border-color: #171717; }

.mp-search-btn {
  padding: 0 16px;
  height: 36px;
  border: none;
  border-radius: 8px;
  background: #171717;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}

/* ─── Product Cards ─── */
.mp-product-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mp-product-card {
  background: #fff;
  border: 1px solid #ebebeb;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 0.15s;
}

.mp-product-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.08); }

.mp-product-img {
  display: block;
  width: 100%;
  height: 150px;
  object-fit: cover;
  background: #f5f5f5;
}

.mp-product-body { padding: 12px; }

.mp-product-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.mp-product-name {
  font-size: 15px;
  font-weight: 600;
  color: #171717;
}

.mp-tag {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 20px;
  background: #fafafa;
  font-size: 11px;
  color: #4d4d4d;
}

.mp-product-desc {
  margin-top: 6px;
  color: #666;
  font-size: 13px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.mp-product-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
}

.mp-price { color: #171717; font-weight: 600; }
.mp-price-lg { font-size: 18px; }
.mp-unit { color: #666; font-size: 13px; }
.mp-stock { color: #666; font-size: 12px; display: block; margin-top: 2px; }
.mp-stock-low { color: #ee0000; }

.mp-add-btn {
  padding: 4px 14px;
  border: none;
  border-radius: 20px;
  background: #171717;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
}

/* ─── Detail ─── */
.mp-detail-img {
  display: block;
  width: calc(100% + 32px);
  margin: -16px -16px 0;
  height: 250px;
  object-fit: cover;
  background: #f5f5f5;
}

.mp-detail-body { padding: 16px 0; }

.mp-detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.mp-detail-name { font-size: 20px; font-weight: 600; color: #171717; }
.mp-detail-price { margin-top: 12px; }
.mp-detail-stock { margin-top: 8px; color: #666; font-size: 13px; }

.mp-detail-desc {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebebeb;
}

.mp-desc-label { font-size: 14px; font-weight: 500; margin-bottom: 6px; }
.mp-desc-text { font-size: 14px; color: #4d4d4d; line-height: 1.7; }

.mp-detail-actions {
  display: flex;
  gap: 10px;
  padding: 12px 0;
  position: sticky;
  bottom: 0;
  background: #fafafa;
}

/* ─── Cart ─── */
.mp-empty-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 16px;
}

.mp-empty-icon { font-size: 48px; }
.mp-empty-text { color: #666; font-size: 14px; }

.mp-cart-list {
  background: #fff;
  border: 1px solid #ebebeb;
  border-radius: 12px;
  overflow: hidden;
}

.mp-cart-item {
  display: flex;
  gap: 10px;
  padding: 12px;
  border-bottom: 1px solid #ebebeb;
}

.mp-cart-item:last-child { border-bottom: none; }

.mp-cart-img {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  object-fit: cover;
  background: #f5f5f5;
  flex-shrink: 0;
}

.mp-cart-info { flex: 1; min-width: 0; }
.mp-cart-name { font-size: 14px; font-weight: 600; color: #171717; }
.mp-muted { color: #666; font-size: 12px; }

.mp-cart-qty {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.mp-qty-btn {
  width: 28px;
  height: 28px;
  border: 1px solid #ebebeb;
  border-radius: 6px;
  background: #fff;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mp-qty-val { font-size: 14px; font-weight: 500; min-width: 20px; text-align: center; }

.mp-remove-btn {
  margin-left: auto;
  border: none;
  background: none;
  color: #ee0000;
  font-size: 12px;
  cursor: pointer;
}

.mp-cart-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #fff;
  border: 1px solid #ebebeb;
  border-radius: 12px;
  margin-top: 12px;
  font-size: 14px;
  color: #4d4d4d;
}

/* ─── Form ─── */
.mp-form-section, .mp-profile-form {
  background: #fff;
  border: 1px solid #ebebeb;
  border-radius: 12px;
  padding: 16px;
  margin-top: 12px;
}

.mp-form-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #171717;
}

.mp-form-field {
  margin-bottom: 12px;
}

.mp-form-field label {
  display: block;
  font-size: 13px;
  color: #4d4d4d;
  margin-bottom: 4px;
}

.mp-form-field input,
.mp-form-field textarea {
  display: block;
  width: 100%;
  border: 1px solid #ebebeb;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  outline: none;
  font-family: inherit;
  background: #fff;
  box-sizing: border-box;
}

.mp-form-field input:focus,
.mp-form-field textarea:focus { border-color: #171717; }

/* ─── Orders ─── */
.mp-order-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mp-order-card {
  background: #fff;
  border: 1px solid #ebebeb;
  border-radius: 12px;
  padding: 14px;
}

.mp-order-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.mp-order-no { font-weight: 600; font-size: 13px; color: #171717; margin-bottom: 2px; }

.mp-status {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.mp-status-success { color: #1a7f37; background: #dafbe1; }
.mp-status-warn { color: #ab570a; background: #ffefcf; }
.mp-status-danger { color: #c50000; background: #f7d4d6; }
.mp-status-info { color: #0070f3; background: #d3e5ff; }

.mp-order-receiver { margin-top: 10px; }
.mp-receiver-name { font-size: 14px; font-weight: 500; }

.mp-order-items {
  margin-top: 10px;
  padding: 8px 0;
  border-top: 1px solid #ebebeb;
  border-bottom: 1px solid #ebebeb;
}

.mp-order-item-line { font-size: 13px; color: #4d4d4d; line-height: 1.6; }

.mp-order-foot {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}

.mp-order-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #ebebeb;
}

/* ─── Buttons ─── */
.mp-primary-btn {
  display: block;
  width: 100%;
  height: 40px;
  border: none;
  border-radius: 20px;
  background: #171717;
  color: #fff;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
}

.mp-primary-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.mp-outline-btn {
  display: block;
  width: 100%;
  height: 40px;
  border: 1px solid #ebebeb;
  border-radius: 20px;
  background: #fff;
  color: #171717;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
}

.mp-btn-sm { height: 32px; font-size: 13px; width: auto; padding: 0 16px; }

/* ─── States ─── */
.mp-loading, .mp-empty {
  padding: 32px;
  text-align: center;
  color: #666;
  font-size: 14px;
}

.mp-tip {
  margin-top: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 12px;
  color: #666;
  font-size: 12px;
  line-height: 1.6;
}

/* ─── Tab Bar ─── */
.phone-tab-bar {
  display: flex;
  height: 50px;
  background: #ffffff;
  border-top: 1px solid #ebebeb;
  flex-shrink: 0;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  cursor: pointer;
  position: relative;
  color: #888;
  transition: color 0.15s;
}

.tab-item.active { color: #171717; }
.tab-icon { font-size: 18px; }
.tab-label { font-size: 10px; }

.tab-badge {
  position: absolute;
  top: 4px;
  right: 50%;
  margin-right: -20px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background: #ee0000;
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
