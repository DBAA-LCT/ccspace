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

export const deliveryTypeLabels = {
  home_delivery: "送货上门",
  self_pickup: "到店自取"
};

export const orderStatusOptions = Object.entries(orderStatusLabels).map(([value, label]) => ({ value, label }));
export const parcelStatusOptions = Object.entries(parcelStatusLabels).map(([value, label]) => ({ value, label }));

export const productColumns = [
  { colKey: "name", title: "商品", minWidth: 240 },
  { colKey: "category", title: "分类", width: 100 },
  { colKey: "priceCents", title: "售价", width: 100 },
  { colKey: "stock", title: "库存", width: 100 },
  { colKey: "status", title: "状态", width: 80 },
  { colKey: "actions", title: "操作", width: 150, fixed: "right" }
];

export const orderColumns = [
  { colKey: "orderNo", title: "订单", width: 160 },
  { colKey: "customer", title: "下单人", width: 130 },
  { colKey: "receiver", title: "收货人", minWidth: 200 },
  { colKey: "items", title: "商品", minWidth: 180 },
  { colKey: "totalCents", title: "金额", width: 90 },
  { colKey: "status", title: "状态", width: 90 },
  { colKey: "actions", title: "更新", width: 200, fixed: "right" }
];

export const parcelColumns = [
  { colKey: "parcelNo", title: "快递", width: 200 },
  { colKey: "receiver", title: "收件人", minWidth: 200 },
  { colKey: "note", title: "备注", minWidth: 150 },
  { colKey: "status", title: "状态", width: 90 },
  { colKey: "actions", title: "更新", width: 200, fixed: "right" }
];

export const adminColumns = [
  { colKey: "username", title: "账号", width: 150 },
  { colKey: "name", title: "昵称", width: 150 },
  { colKey: "role", title: "角色", width: 100 },
  { colKey: "createdAt", title: "创建时间", width: 180 },
  { colKey: "actions", title: "操作", width: 150 }
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

export function statusBadgeClass(status, themeFn) {
  const theme = themeFn(status);
  return { success: "badge-success", danger: "badge-error", primary: "badge-info", warning: "badge-warning" }[theme] || "badge-warning";
}
