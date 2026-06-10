Page({
  data: {
    profile: {}
  },

  onShow() {
    this.setData({
      profile: getApp().globalData.profile || {}
    });
  },

  saveProfile(event) {
    getApp().saveProfile(event.detail.value);
    this.setData({ profile: event.detail.value });
    wx.showToast({ title: "已保存", icon: "success" });
  }
});

