const api = require("../../utils/api");

Page({
  data: {
    profile: {},
    reminders: [],
    monthlyStats: [],
    totalSpent: "0.00"
  },

  onShow() {
    const profile = getApp().globalData.profile || {};
    this.setData({ profile });
    if (profile.customerPhone) {
      this.loadReminders(profile.customerPhone);
      this.loadStats(profile.customerPhone);
    }
  },

  loadReminders(phone) {
    api.request(`/api/reminders?phone=${encodeURIComponent(phone)}`).then(reminders => {
      this.setData({ reminders });
    }).catch(() => {});
  },

  loadStats(phone) {
    api.request(`/api/stats/monthly?phone=${encodeURIComponent(phone)}`).then(monthlyStats => {
      const totalCents = monthlyStats.reduce((sum, m) => sum + m.totalCents, 0);
      this.setData({
        monthlyStats,
        totalSpent: api.yuan(totalCents)
      });
    }).catch(() => {});
  },

  saveProfile(event) {
    const values = event.detail.value;
    getApp().saveProfile(values);
    this.setData({ profile: values });
    wx.showToast({ title: "已保存", icon: "success" });
    if (values.customerPhone) {
      this.loadReminders(values.customerPhone);
      this.loadStats(values.customerPhone);
    }
  },

  deleteReminder(event) {
    const id = event.currentTarget.dataset.id;
    wx.showModal({
      title: "取消提醒",
      content: "确定取消这个定期提醒吗？",
      success: (res) => {
        if (res.confirm) {
          api.request(`/api/reminders/${id}`, { method: "DELETE" }).then(() => {
            this.setData({ reminders: this.data.reminders.filter(r => r.id !== id) });
            wx.showToast({ title: "已取消", icon: "success" });
          }).catch(() => {});
        }
      }
    });
  }
});
