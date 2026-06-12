const api = require("../../utils/api");

Page({
  data: {
    loading: true,
    product: null,
    cartCount: 0,
    reviews: [],
    reminderSet: false
  },

  onLoad(options) {
    if (options.id) {
      this.loadProduct(options.id);
      this.loadReviews(options.id);
    }
    this.updateCartCount();
  },

  loadProduct(id) {
    this.setData({ loading: true });
    api.request(`/api/products/${id}`)
      .then(product => {
        this.setData({
          product: {
            ...product,
            priceYuan: api.yuan(product.priceCents),
            originalPriceYuan: product.originalPriceCents ? api.yuan(product.originalPriceCents) : "",
            hasDiscount: product.originalPriceCents && product.originalPriceCents > product.priceCents,
            ratingText: product.avgRating > 0 ? product.avgRating.toFixed(1) : ""
          },
          loading: false
        });
      })
      .catch(error => {
        this.setData({ loading: false, product: null });
        wx.showToast({ title: error.message || "加载失败", icon: "none" });
      });
  },

  loadReviews(productId) {
    api.request(`/api/products/${productId}/reviews`).then(reviews => {
      this.setData({ reviews });
    }).catch(() => {});
  },

  setReminder() {
    const product = this.data.product;
    if (!product) return;
    const profile = getApp().globalData.profile || {};
    const phone = profile.customerPhone;
    if (!phone) {
      wx.showToast({ title: "请先在「我的」页面填写手机号", icon: "none" });
      return;
    }
    api.request(`/api/reminders?phone=${encodeURIComponent(phone)}`, {
      method: "POST",
      data: { productId: Number(product.id), intervalDays: 30 }
    }).then(() => {
      this.setData({ reminderSet: true });
      wx.showToast({ title: "已设置每月提醒", icon: "success" });
    }).catch(error => {
      wx.showToast({ title: error.message || "设置失败", icon: "none" });
    });
  },

  updateCartCount() {
    const cart = getApp().globalData.cart || [];
    const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);
    this.setData({ cartCount });
    getApp().updateCartBadge();
  },

  addToCart() {
    const product = this.data.product;
    if (!product) return;

    const app = getApp();
    const cart = [...(app.globalData.cart || [])];
    const existing = cart.find(item => item.id === product.id);
    if (existing) {
      if (existing.quantity >= product.stock) {
        wx.showToast({ title: "库存不够了", icon: "none" });
        return;
      }
      existing.quantity += 1;
    } else {
      cart.push({
        id: product.id,
        name: product.name,
        priceCents: product.priceCents,
        priceYuan: product.priceYuan,
        unit: product.unit,
        stock: product.stock,
        imageUrl: product.imageUrl,
        quantity: 1
      });
    }
    app.saveCart(cart);
    this.updateCartCount();
    wx.showToast({ title: "已加入购物车", icon: "success" });
  },

  goCart() {
    wx.switchTab({ url: "/pages/cart/cart" });
  }
});
