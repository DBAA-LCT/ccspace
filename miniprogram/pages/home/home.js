const api = require("../../utils/api");

Page({
  data: {
    loading: true,
    products: [],
    hotProducts: [],
    cartCount: 0,
    searchKey: "",
    hotSearches: []
  },

  onShow() {
    this.updateCartCount();
    this.loadProducts();
    this.loadHot();
  },

  onPullDownRefresh() {
    Promise.all([this.loadProducts(), this.loadHot()]).finally(() => wx.stopPullDownRefresh());
  },

  loadProducts() {
    this.setData({ loading: true });
    let url = "/api/products?status=on_sale";
    if (this.data.searchKey) {
      url += "&q=" + encodeURIComponent(this.data.searchKey);
      api.request("/api/search/log", { method: "POST", data: { keyword: this.data.searchKey } }).catch(() => {});
    }
    return api.request(url)
      .then(products => {
        this.setData({
          products: products.map(item => ({
            ...item,
            priceYuan: api.yuan(item.priceCents),
            originalPriceYuan: item.originalPriceCents ? api.yuan(item.originalPriceCents) : "",
            hasDiscount: item.originalPriceCents && item.originalPriceCents > item.priceCents,
            ratingText: item.avgRating > 0 ? item.avgRating.toFixed(1) : ""
          })),
          loading: false
        });
      })
      .catch(error => {
        this.setData({ loading: false, products: [] });
        wx.showToast({ title: error.message || "加载失败", icon: "none" });
      });
  },

  loadHot() {
    api.request("/api/products/hot?limit=6").then(hotProducts => {
      this.setData({
        hotProducts: hotProducts.map(item => ({
          ...item,
          priceYuan: api.yuan(item.priceCents)
        }))
      });
    }).catch(() => {});
    api.request("/api/search/hot?limit=6").then(hotSearches => {
      this.setData({ hotSearches });
    }).catch(() => {});
  },

  onSearchInput(event) {
    this.setData({ searchKey: event.detail.value });
  },

  onSearchConfirm() {
    this.loadProducts();
  },

  onSearchClear() {
    this.setData({ searchKey: "" });
    this.loadProducts();
  },

  onHotSearch(event) {
    this.setData({ searchKey: event.currentTarget.dataset.keyword });
    this.loadProducts();
  },

  updateCartCount() {
    const cart = getApp().globalData.cart || [];
    const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);
    this.setData({ cartCount });
    getApp().updateCartBadge();
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

  goDetail(event) {
    const id = event.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` });
  },

  goCart() {
    wx.switchTab({ url: "/pages/cart/cart" });
  }
});
