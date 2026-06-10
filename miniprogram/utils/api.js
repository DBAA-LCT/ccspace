const API_BASE = "http://119.45.182.166:3784";

function request(path, options = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${API_BASE}${path}`,
      method: options.method || "GET",
      data: options.data || {},
      header: {
        "content-type": "application/json"
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data.data || res.data);
          return;
        }
        reject(new Error((res.data && res.data.error) || "请求失败"));
      },
      fail(error) {
        reject(new Error(error.errMsg || "网络异常"));
      }
    });
  });
}

function yuan(cents) {
  return (Number(cents || 0) / 100).toFixed(2);
}

module.exports = {
  request,
  yuan,
  API_BASE
};
