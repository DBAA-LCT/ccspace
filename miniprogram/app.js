App({
  globalData: {
    cart: [],
    profile: {}
  },

  onLaunch() {
    this.globalData.cart = wx.getStorageSync("cart") || [];
    this.globalData.profile = wx.getStorageSync("profile") || {};
  },

  saveCart(cart) {
    this.globalData.cart = cart;
    wx.setStorageSync("cart", cart);
  },

  saveProfile(profile) {
    this.globalData.profile = profile;
    wx.setStorageSync("profile", profile);
  }
});

