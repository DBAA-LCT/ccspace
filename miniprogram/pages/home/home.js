const api = require("../../utils/api");

Page({
  data: {
    loading: true,
    products: [],
    cartCount: 0
  },

  onShow() {
    this.updateCartCount();
    this.loadProducts();
  },

  onPullDownRefresh() {
    this.loadProducts().finally(() => wx.stopPullDownRefresh());
  },

  loadProducts() {
    this.setData({ loading: true });
    return api.request("/api/products?status=on_sale")
      .then(products => {
        this.setData({
          products: products.map(item => ({
            ...item,
            priceYuan: api.yuan(item.priceCents)
          })),
          loading: false
        });
      })
      .catch(error => {
        this.setData({ loading: false, products: [] });
        wx.showToast({ title: error.message || "加载失败", icon: "none" });
      });
  },

  updateCartCount() {
    const cart = getApp().globalData.cart || [];
    const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);
    this.setData({ cartCount });
  },

  addToCart(event) {
    const product = this.data.products.find(item => item.id === event.currentTarget.dataset.id);
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
