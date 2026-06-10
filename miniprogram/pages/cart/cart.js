const api = require("../../utils/api");

Page({
  data: {
    cart: [],
    totalYuan: "0.00",
    profile: {},
    submitting: false
  },

  onShow() {
    this.refresh();
  },

  refresh() {
    const app = getApp();
    const cart = app.globalData.cart || [];
    const totalCents = cart.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
    this.setData({
      cart,
      totalYuan: api.yuan(totalCents),
      profile: app.globalData.profile || {}
    });
  },

  saveCart(cart) {
    getApp().saveCart(cart);
    this.refresh();
  },

  changeQuantity(event) {
    const cart = [...this.data.cart];
    const item = cart.find(entry => entry.id === event.currentTarget.dataset.id);
    if (!item) return;
    item.quantity = Number(event.detail.value);
    this.saveCart(cart);
  },

  remove(event) {
    this.saveCart(this.data.cart.filter(entry => entry.id !== event.currentTarget.dataset.id));
  },

  async submitOrder(event) {
    const values = event.detail.value;
    const requiredFields = ["customerName", "customerPhone", "receiverName", "receiverPhone", "address"];
    const missing = requiredFields.some(field => !String(values[field] || "").trim());
    if (missing) {
      wx.showToast({ title: "请补全联系人和地址", icon: "none" });
      return;
    }

    this.setData({ submitting: true });
    try {
      const order = await api.request("/api/orders", {
        method: "POST",
        data: {
          ...values,
          deliveryType: "home_delivery",
          items: this.data.cart.map(item => ({
            productId: item.id,
            quantity: item.quantity
          }))
        }
      });
      getApp().saveProfile(values);
      getApp().saveCart([]);
      wx.showModal({
        title: "下单成功",
        content: `订单号：${order.orderNo}`,
        showCancel: false,
        success() {
          wx.switchTab({ url: "/pages/orders/orders" });
        }
      });
    } catch (error) {
      wx.showToast({ title: error.message, icon: "none" });
    } finally {
      this.setData({ submitting: false });
    }
  },

  goHome() {
    wx.switchTab({ url: "/pages/home/home" });
  }
});
