const api = require("../../utils/api");

const statusLabels = {
  pending: "待确认",
  confirmed: "待配送",
  delivering: "配送中",
  completed: "已完成",
  cancelled: "已取消"
};

function statusClass(status) {
  if (status === "completed") return "status success";
  if (status === "cancelled") return "status danger";
  if (status === "delivering") return "status info";
  return "status warn";
}

Page({
  data: {
    phone: "",
    loading: false,
    orders: []
  },

  onShow() {
    const profile = getApp().globalData.profile || {};
    const phone = profile.customerPhone || this.data.phone;
    this.setData({ phone });
    if (phone) {
      this.loadOrders(phone);
    }
  },

  onPullDownRefresh() {
    this.loadOrders(this.data.phone).finally(() => wx.stopPullDownRefresh());
  },

  searchOrders(event) {
    const phone = event.detail.value.phone;
    this.setData({ phone });
    if (phone) {
      this.loadOrders(phone);
    }
  },

  loadOrders(phone) {
    if (!phone) {
      this.setData({ orders: [], loading: false });
      return Promise.resolve();
    }
    this.setData({ loading: true });
    return api.request(`/api/orders?phone=${encodeURIComponent(phone)}`)
      .then(orders => {
        this.setData({
          orders: orders.map(order => ({
            ...order,
            totalYuan: api.yuan(order.totalCents),
            statusText: statusLabels[order.status] || order.status,
            statusClass: statusClass(order.status),
            canCancel: order.status === "pending" || order.status === "confirmed",
            canReview: order.status === "completed",
            hasPhoto: !!order.deliveryPhoto,
            createdText: new Date(order.createdAt).toLocaleString()
          })),
          loading: false
        });
      })
      .catch(error => {
        this.setData({ loading: false, orders: [] });
        wx.showToast({ title: error.message || "加载失败", icon: "none" });
      });
  },

  cancelOrder(event) {
    const id = event.currentTarget.dataset.id;
    const order = this.data.orders.find(o => o.id === id);
    if (!order) return;
    wx.showModal({
      title: "确认取消",
      content: `确定要取消订单 ${order.orderNo} 吗？取消后库存将恢复。`,
      success: (res) => {
        if (res.confirm) {
          api.request(`/api/orders/${id}/cancel`, { method: "PATCH" })
            .then(() => {
              wx.showToast({ title: "订单已取消", icon: "success" });
              this.loadOrders(this.data.phone);
            })
            .catch(error => {
              wx.showToast({ title: error.message || "取消失败", icon: "none" });
            });
        }
      }
    });
  },

  reorder(event) {
    const id = event.currentTarget.dataset.id;
    api.request(`/api/orders/${id}/reorder`)
      .then(items => {
        const app = getApp();
        const cart = [...(app.globalData.cart || [])];
        let addedCount = 0;
        items.forEach(item => {
          const existing = cart.find(c => c.id === item.productId);
          if (existing) {
            existing.quantity += item.quantity;
          } else {
            cart.push({
              id: item.productId,
              name: item.name,
              priceCents: item.priceCents,
              priceYuan: api.yuan(item.priceCents),
              unit: item.unit,
              stock: 999,
              imageUrl: "",
              quantity: item.quantity
            });
          }
          addedCount++;
        });
        app.saveCart(cart);
        wx.showToast({ title: `已加入${addedCount}件商品`, icon: "success" });
        setTimeout(() => {
          wx.switchTab({ url: "/pages/cart/cart" });
        }, 1000);
      })
      .catch(error => {
        wx.showToast({ title: error.message || "操作失败", icon: "none" });
      });
  },

  viewPhoto(event) {
    const url = event.currentTarget.dataset.url;
    if (url) {
      wx.previewImage({ urls: [url], current: url });
    }
  }
});
