# API 文档

基础地址：

```text
http://localhost:3784
```

成功响应：

```json
{ "data": {} }
```

错误响应：

```json
{ "error": "错误信息" }
```

分页响应：

```json
{ "data": [], "total": 100, "page": 1, "pageSize": 20 }
```

---

## 管理端登录

```http
POST /api/admin/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123456"
}
```

返回 `token` 后，管理端接口需要携带：

```http
Authorization: Bearer <token>
```

## 管理员管理

```http
GET  /api/admin/me                    # 获取当前管理员信息
POST /api/admin/change-password       # 修改密码
GET  /api/admin/admins                # 管理员列表（仅店主）
POST /api/admin/admins                # 创建管理员（仅店主）
PUT  /api/admin/admins/:id            # 修改管理员（仅店主）
DELETE /api/admin/admins/:id          # 删除管理员（仅店主）
```

## 商品接口

公开查询：

```http
GET /api/products
GET /api/products?status=on_sale
GET /api/products?q=大米
GET /api/products?category=粮油副食
GET /api/products/categories          # 获取所有分类
GET /api/products/:id                 # 商品详情
```

管理端：

```http
GET    /api/admin/products?page=1&page_size=20&q=&status=&category=
POST   /api/admin/products            # 新增
PUT    /api/admin/products/:id         # 全量更新
PATCH  /api/admin/products/:id         # 部分更新
PATCH  /api/admin/products/:id/status  # 上下架
DELETE /api/admin/products/:id         # 删除（无关联订单时）
```

## 订单接口

小程序查询订单：

```http
GET /api/orders?phone=13800000001
```

创建订单：

```http
POST /api/orders
Content-Type: application/json

{
  "customerName": "张先生",
  "customerPhone": "13800000001",
  "receiverName": "张奶奶",
  "receiverPhone": "13900000001",
  "address": "幸福村三组12号",
  "deliveryType": "home_delivery",
  "note": "和快递一起送",
  "items": [{ "productId": 1, "quantity": 1 }]
}
```

用户取消订单（pending/confirmed 状态可取消）：

```http
PATCH /api/orders/:id/cancel
```

管理端：

```http
GET   /api/admin/orders?page=1&page_size=20&q=&status=
PATCH /api/admin/orders/:id/status
```

订单状态流转：

```
pending → confirmed → delivering → completed
   ↓         ↓           ↓
cancelled cancelled  cancelled
```

## 快递接口

```http
GET   /api/admin/parcels?page=1&page_size=20&q=&status=
POST  /api/admin/parcels
PATCH /api/admin/parcels/:id/status
DELETE /api/admin/parcels/:id    # 仅待配送/已取消可删除
```

快递状态流转：

```
pending → delivering → completed
   ↓          ↓
cancelled  cancelled
```

## 仪表盘统计

```http
GET /api/admin/summary
```

返回：

```json
{
  "data": {
    "productCount": 10,
    "onSaleCount": 8,
    "pendingOrderCount": 3,
    "pendingParcelCount": 2,
    "revenueCents": 125000,
    "todayOrderCount": 5
  }
}
```

## 健康检查

```http
GET /health
```

---

## 订单状态说明

| 状态 | 含义 | 可流转到 |
|------|------|----------|
| `pending` | 待确认 | confirmed, cancelled |
| `confirmed` | 待配送 | delivering, cancelled |
| `delivering` | 配送中 | completed, cancelled |
| `completed` | 已完成 | — |
| `cancelled` | 已取消 | — |

## 快递状态说明

| 状态 | 含义 | 可流转到 |
|------|------|----------|
| `pending` | 待配送 | delivering, cancelled |
| `delivering` | 配送中 | completed, cancelled |
| `completed` | 已送达 | — |
| `cancelled` | 已取消 | — |
