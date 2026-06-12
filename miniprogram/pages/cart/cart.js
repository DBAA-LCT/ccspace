const api = require("../../utils/api");

Page({
  data: {
    cart: [],
    totalYuan: "0.00",
    profile: {},
    formData: {},
    submitting: false,
    noteTemplates: [],
    deliveryDates: [],
    selectedDateIndex: 0,
    promotions: []
  },

  onShow() {
    this.refresh();
    this.loadTemplates();
    this.loadPromotions();
    this.initDeliveryDates();
  },

  refresh() {
    const app = getApp();
    const cart = app.globalData.cart || [];
    const totalCents = cart.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
    const profile = app.globalData.profile || {};
    this.setData({
      cart,
      totalYuan: api.yuan(totalCents),
      profile,
      formData: { ...profile, deliveryDate: this.data.deliveryDates[this.data.selectedDateIndex] || "" }
    });
  },

  loadTemplates() {
    api.request("/api/note-templates").then(noteTemplates => {
      this.setData({ noteTemplates });
    }).catch(() => {});
  },

  loadPromotions() {
    api.request("/api/promotions").then(promotions => {
      this.setData({ promotions });
    }).catch(() => {});
  },

  initDeliveryDates() {
    const dates = [];
    const today = new Date();
    for (let i = 0; i < 7; i++) {
      const d = new Date(today);
      d.setDate(d.getDate() + i);
      const label = i === 0 ? "尽快送达" : i === 1 ? "明天" : `${d.getMonth() + 1}月${d.getDate()}日`;
      const value = d.toISOString().split("T")[0];
      dates.push({ label, value });
    }
    this.setData({ deliveryDates: dates });
  },

  onSelectDate(event) {
    const index = event.currentTarget.dataset.index;
    this.setData({
      selectedDateIndex: index,
      "formData.deliveryDate": this.data.deliveryDates[index].value
    });
  },

  onFieldChange(event) {
    const field = event.currentTarget.dataset.field;
    if (field) {
      this.setData({ [`formData.${field}`]: event.detail.value });
    }
  },

  onNoteTemplate(event) {
    const text = event.currentTarget.dataset.text;
    const current = this.data.formData.note || "";
    this.setData({ "formData.note": current ? current + "，" + text : text });
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
    const id = event.currentTarget.dataset.id;
    const item = this.data.cart.find(entry => entry.id === id);
    if (!item) return;
    wx.showModal({
      title: "确认移除",
      content: `确定要从购物车移除「${item.name}」吗？`,
      success: (res) => {
        if (res.confirm) {
          this.saveCart(this.data.cart.filter(entry => entry.id !== id));
          wx.showToast({ title: "已移除", icon: "success" });
        }
      }
    });
  },

  validatePhone(phone) {
    return /^1[3-9]\d{9}$/.test(phone);
  },

  submitOrder() {
    const values = this.data.formData;
    const requiredFields = ["customerName", "customerPhone", "receiverName", "receiverPhone", "address"];
    const missing = requiredFields.some(field => !String(values[field] || "").trim());
    if (missing) {
      wx.showToast({ title: "请补全联系人和地址", icon: "none" });
      return;
    }
    if (!this.validatePhone(values.customerPhone)) {
      wx.showToast({ title: "下单人手机号格式不正确", icon: "none" });
      return;
    }
    if (!this.validatePhone(values.receiverPhone)) {
      wx.showToast({ title: "收货人电话格式不正确", icon: "none" });
      return;
    }

    this.setData({ submitting: true });
    api.request("/api/orders", {
      method: "POST",
      data: {
        ...values,
        deliveryType: "home_delivery",
        deliveryDate: values.deliveryDate || "",
        items: this.data.cart.map(item => ({
          productId: item.id,
          quantity: item.quantity
        }))
      }
    })
      .then(order => {
        getApp().saveProfile(values);
        getApp().saveCart([]);
        wx.showModal({
          title: "下单成功",
          content: "订单号：" + order.orderNo,
          showCancel: false,
          success() {
            wx.switchTab({ url: "/pages/orders/orders" });
          }
        });
      })
      .catch(error => {
        wx.showToast({ title: error.message || "下单失败", icon: "none" });
      })
      .finally(() => {
        this.setData({ submitting: false });
      });
  },

  goHome() {
    wx.switchTab({ url: "/pages/home/home" });
  }
});
