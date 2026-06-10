export const productStatusLabels = {
  on_sale: "上架",
  off_shelf: "下架"
};

export const orderStatusLabels = {
  pending: "待确认",
  confirmed: "待配送",
  delivering: "配送中",
  completed: "已完成",
  cancelled: "已取消"
};

export const parcelStatusLabels = {
  pending: "待配送",
  delivering: "配送中",
  completed: "已送达",
  cancelled: "已取消"
};

export const orderStatusOptions = Object.entries(orderStatusLabels).map(([value, label]) => ({ value, label }));
export const parcelStatusOptions = Object.entries(parcelStatusLabels).map(([value, label]) => ({ value, label }));

export const productColumns = [
  { colKey: "name", title: "商品", width: 320 },
  { colKey: "category", title: "分类", width: 110 },
  { colKey: "priceCents", title: "售价", width: 100 },
  { colKey: "stock", title: "库存", width: 100 },
  { colKey: "status", title: "状态", width: 90 },
  { colKey: "actions", title: "操作", width: 150 }
];

export const orderColumns = [
  { colKey: "orderNo", title: "订单", width: 160 },
  { colKey: "customerName", title: "下单人", width: 140 },
  { colKey: "receiver", title: "收货老人", width: 280 },
  { colKey: "items", title: "商品", width: 220 },
  { colKey: "totalCents", title: "金额", width: 100 },
  { colKey: "status", title: "状态", width: 100 },
  { colKey: "actions", title: "更新", width: 210 }
];

export const parcelColumns = [
  { colKey: "parcelNo", title: "快递", width: 220 },
  { colKey: "receiver", title: "收件人", width: 280 },
  { colKey: "note", title: "备注", width: 220 },
  { colKey: "status", title: "状态", width: 100 },
  { colKey: "actions", title: "更新", width: 210 }
];

export function orderTheme(status) {
  if (status === "completed") return "success";
  if (status === "cancelled") return "danger";
  if (status === "delivering") return "primary";
  return "warning";
}

export function parcelTheme(status) {
  if (status === "completed") return "success";
  if (status === "cancelled") return "danger";
  if (status === "delivering") return "primary";
  return "warning";
}
