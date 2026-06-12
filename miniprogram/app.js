App({
  globalData: {
    cart: [],
    profile: {}
  },

  onLaunch() {
    try {
      this.globalData.cart = wx.getStorageSync("cart") || [];
      this.globalData.profile = wx.getStorageSync("profile") || {};
    } catch (e) {
      console.error("读取本地存储失败", e);
    }
    this.updateCartBadge();
  },

  onError(err) {
    console.error("全局错误:", err);
  },

  saveCart(cart) {
    this.globalData.cart = cart;
    try {
      wx.setStorageSync("cart", cart);
    } catch (e) {
      console.error("保存购物车失败", e);
    }
    this.updateCartBadge();
  },

  saveProfile(profile) {
    this.globalData.profile = profile;
    try {
      wx.setStorageSync("profile", profile);
    } catch (e) {
      console.error("保存用户信息失败", e);
    }
  },

  updateCartBadge() {
    const cart = this.globalData.cart || [];
    const count = cart.reduce((sum, item) => sum + item.quantity, 0);
    if (count > 0) {
      wx.setTabBarBadge({ index: 1, text: String(count) });
    } else {
      wx.removeTabBarBadge({ index: 1 });
    }
  }
});
