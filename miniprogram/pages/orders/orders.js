const api = require("../../utils/api");

const statusLabels = {
  pending: "待确认",
  confirmed: "待配送",
  delivering: "配送中",
  completed: "已完成",
  cancelled: "已取消"
};

function statusClass(status) {
  if (status === "completed") return "status-success";
  if (status === "cancelled") return "status-error";
  if (status === "delivering") return "status-info";
  return "status-warning";
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
            createdText: new Date(order.createdAt).toLocaleString()
          })),
          loading: false
        });
      })
      .catch(error => {
        this.setData({ loading: false, orders: [] });
        wx.showToast({ title: error.message || "加载失败", icon: "none" });
      });
  }
});
