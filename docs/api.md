# API 文档

基础地址：

```text
http://localhost:3784
```

服务器部署后通常为：

```text
http://119.45.182.166:3784
```

成功响应：

```json
{
  "data": {}
}
```

错误响应：

```json
{
  "error": "错误信息"
}
```

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

## 商品接口

公开查询：

```http
GET /api/products
GET /api/products?status=on_sale
GET /api/products?q=大米
GET /api/products/:id
```

管理端新增商品：

```http
POST /api/admin/products
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "东北珍珠米 10斤",
  "category": "粮油副食",
  "priceCents": 3900,
  "stock": 12,
  "unit": "袋",
  "imageUrl": "https://example.com/rice.jpg",
  "description": "适合家庭日常煮饭",
  "status": "on_sale"
}
```

管理端更新商品：

```http
PUT /api/admin/products/:id
PATCH /api/admin/products/:id/status
```

## 订单接口

小程序查询自己的订单：

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
  "address": "幸福村三组老槐树旁",
  "deliveryType": "home_delivery",
  "note": "和快递一起送",
  "items": [
    {
      "productId": 1,
      "quantity": 1
    }
  ]
}
```

创建订单会扣减库存；订单改为 `cancelled` 时会回补库存。

管理端查询订单：

```http
GET /api/admin/orders
GET /api/admin/orders?status=pending
```

管理端修改订单状态：

```http
PATCH /api/admin/orders/:id/status
Content-Type: application/json

{
  "status": "delivering"
}
```

订单状态：

```text
pending      待确认
confirmed    待配送
delivering   配送中
completed    已完成
cancelled    已取消
```

## 快递接口

管理端查询快递：

```http
GET /api/admin/parcels
GET /api/admin/parcels?status=pending
```

登记快递：

```http
POST /api/admin/parcels
Content-Type: application/json

{
  "receiverName": "张奶奶",
  "receiverPhone": "13900000001",
  "carrier": "中通快递",
  "trackingNo": "ZT1234567890",
  "pickupCode": "3-12",
  "address": "幸福村三组老槐树旁",
  "note": "可和订单一起配送"
}
```

修改快递状态：

```http
PATCH /api/admin/parcels/:id/status
Content-Type: application/json

{
  "status": "completed"
}
```

快递状态：

```text
pending      待配送
delivering   配送中
completed    已送达
cancelled    已取消
```

