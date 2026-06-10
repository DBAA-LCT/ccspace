const api = require("../../utils/api");

const statusLabels = {
  pending: "待确认",
  confirmed: "待配送",
  delivering: "配送中",
  completed: "已完成",
  cancelled: "已取消"
};

function statusTheme(status) {
  if (status === "completed") return "success";
  if (status === "cancelled") return "danger";
  if (status === "delivering") return "primary";
  return "warning";
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
    this.loadOrders(phone);
  },

  onPullDownRefresh() {
    this.loadOrders(this.data.phone).finally(() => wx.stopPullDownRefresh());
  },

  searchOrders(event) {
    const phone = event.detail.value.phone;
    this.setData({ phone });
    this.loadOrders(phone);
  },

  async loadOrders(phone) {
    if (!phone) {
      this.setData({ orders: [], loading: false });
      return;
    }
    this.setData({ loading: true });
    try {
      const orders = await api.request(`/api/orders?phone=${encodeURIComponent(phone)}`);
      this.setData({
        orders: orders.map(order => ({
          ...order,
          totalYuan: api.yuan(order.totalCents),
          statusText: statusLabels[order.status] || order.status,
          statusTheme: statusTheme(order.status),
          createdText: new Date(order.createdAt).toLocaleString()
        })),
        loading: false
      });
    } catch (error) {
      this.setData({ loading: false });
      wx.showToast({ title: error.message, icon: "none" });
    }
  }
});
