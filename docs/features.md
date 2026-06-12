# 功能设计方案

本文档为 CCspace 系统的功能设计规划，涵盖需要新增的核心功能模块、数据模型变更、API 设计和前端交互方案。

---

## 一、用户认证体系（微信登录）

### 背景
当前小程序无用户身份，订单通过手机号查询，任何人知道手机号即可查看全部订单，存在隐私泄露风险。

### 数据模型
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    openid VARCHAR(128) UNIQUE NOT NULL,
    nickname VARCHAR(64) DEFAULT '',
    phone VARCHAR(32) DEFAULT '',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

### API 设计
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 小程序登录，传 `code`，后端换 openid，返回 token |
| GET  | `/api/auth/me` | 获取当前用户信息 |
| PUT  | `/api/auth/profile` | 更新用户昵称、手机号 |

### 小程序交互
- `app.js` 的 `onLaunch` 中调用 `wx.login()` 获取 code
- 登录成功后将 token 存入 `wx.setStorageSync`
- 后续请求自动携带 `Authorization: Bearer <token>`
- 订单查询从 `/api/orders?phone=xxx` 改为 `/api/orders`（根据 token 识别用户）

### 安全改进
- 订单接口必须登录后才能查询自己的订单
- 管理端仍使用独立的账号密码认证

---

## 二、收货地址簿

### 背景
一个用户可能给家里多位亲人买东西，需要维护多个收货地址。

### 数据模型
```sql
CREATE TABLE addresses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    name VARCHAR(80) NOT NULL COMMENT '收货人姓名',
    phone VARCHAR(32) NOT NULL COMMENT '收货人电话',
    address VARCHAR(255) NOT NULL COMMENT '详细地址',
    note VARCHAR(255) DEFAULT '' COMMENT '备注（如：和邻居一起送）',
    is_default TINYINT DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### API 设计
| 方法 | 路径 | 说明 |
|------|------|------|
| GET    | `/api/addresses` | 获取当前用户的所有地址 |
| POST   | `/api/addresses` | 新增地址 |
| PUT    | `/api/addresses/:id` | 修改地址 |
| DELETE | `/api/addresses/:id` | 删除地址 |

### 小程序交互
- 购物车页面的"收货人"字段改为从地址簿选择
- 地址簿页面（新增 tab 或从"我的"进入）支持增删改
- 下单时弹出地址选择列表，一键填充
- 设置默认地址后下单自动填充

---

## 三、商品图片上传

### 背景
当前管理端添加商品时需要手动填写图片 URL，不便于操作。

### 技术方案
- 后端新增 `/api/admin/upload` 接口，接收图片文件
- 存储方案：本地文件系统（开发环境）或对象存储 COS/S3（生产环境）
- 返回可访问的图片 URL

### API 设计
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/admin/upload` | 上传图片，返回 `{ "url": "https://..." }` |

### 管理端交互
- 商品编辑表单的"图片地址"改为图片上传组件
- 支持拖拽上传、预览、替换
- 上传中显示进度条
- 保留 URL 输入方式作为备选

---

## 四、支付与订单确认流程

### 背景
当前系统无支付环节，订单提交后直接进入待确认状态。考虑到农村场景，需要支持多种付款方式。

### 设计方案
支持两种模式（管理端可配置）：

**模式 A：线下付款**
- 用户下单时选择"货到付款"
- 管理员确认订单后安排配送
- 配送完成后标记为已收款

**模式 B：微信支付（后续）**
- 接入微信支付 JSAPI
- 下单后生成支付单，用户完成支付
- 支付成功回调更新订单状态

### 订单状态扩展
```
pending → confirmed → delivering → completed
                ↓                       ↓
           waiting_pay ──→ paid ──→ delivered → completed
```

### API 变更
- `POST /api/orders` 新增 `paymentMethod` 字段（`cod` / `wechat`）
- `PATCH /api/admin/orders/:id/status` 扩展状态流转
- 新增 `PATCH /api/admin/orders/:id/receipt` 标记已收款

---

## 五、订阅消息（订单状态通知）

### 背景
用户下单后无法及时知道订单状态变化，需要主动查询。

### 技术方案
- 使用微信小程序订阅消息（一次性订阅）
- 在下单、查看订单时引导用户授权
- 后端在订单状态变更时发送模板消息

### 消息模板
| 场景 | 模板内容 |
|------|----------|
| 订单确认 | 您的订单 {{order_no}} 已确认，预计 {{time}} 送达 |
| 开始配送 | 您的订单 {{order_no}} 正在配送中 |
| 订单完成 | 您的订单 {{order_no}} 已送达，请查收 |

### 后端变更
- 新增 `notification_queue` 表，记录待发送消息
- 订单状态变更时写入队列
- 定时任务消费队列，调用微信 API 发送

---

## 六、管理端操作日志

### 背景
多人管理时需要追溯谁在什么时候做了什么操作。

### 数据模型
```sql
CREATE TABLE operation_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT NOT NULL,
    action VARCHAR(80) NOT NULL COMMENT '操作类型',
    target_type VARCHAR(40) NOT NULL COMMENT '操作对象类型',
    target_id INT COMMENT '操作对象ID',
    detail TEXT DEFAULT '' COMMENT '操作详情',
    created_at DATETIME NOT NULL,
    FOREIGN KEY (admin_id) REFERENCES admins(id)
);
```

### 记录的操作
- 管理员登录/登出
- 商品新增/编辑/上下架/删除
- 订单状态变更
- 快递登记/状态变更
- 管理员账号变更

### 管理端交互
- 新增"操作日志"页面（仅店主可见）
- 支持按时间、管理员、操作类型筛选
- 表格展示：时间、操作人、操作内容、对象

---

## 七、营收统计与库存预警

### 背景
店主需要了解经营状况，及时补货。

### Dashboard 增强
- **营收趋势图**：近 7 天 / 30 天的订单金额折线图
- **热销商品排行**：按销量排序的 Top 10 商品
- **库存预警列表**：库存 ≤ N 的商品高亮提示（N 可配置，默认 5）
- **订单分布**：各状态订单的饼图/环形图

### API 设计
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/stats/revenue?days=7` | 营收趋势数据 |
| GET | `/api/admin/stats/products?limit=10` | 热销商品排行 |
| GET | `/api/admin/stats/low-stock?threshold=5` | 低库存商品列表 |

### 管理端交互
- Dashboard 页面使用 ECharts 或类似图表库
- 营收趋势为可切换的日/周/月视图
- 低库存商品支持一键跳转到商品编辑

---

## 八、快递扫码登记

### 背景
当前快递登记需要手动输入运单号，效率低。

### 技术方案
- 管理端使用手机扫码（通过小程序端的管理功能，或 Web 端调用摄像头）
- 扫描快递面单上的条形码/二维码
- 自动识别运单号，关联快递公司

### 小程序管理端（可选）
- 新增管理功能页面（仅管理员可见）
- 调用 `wx.scanCode()` 扫描快递条码
- 扫码后自动填充运单号，手动选择快递公司和收件人

### API 变更
- `POST /api/admin/parcels` 支持 `trackingNo` 自动识别快递公司

---

## 九、配送路线汇总

### 背景
小店管理员配送时需要规划路线，当前系统没有按地址分组的功能。

### 设计方案
- 管理端新增"配送单"视图
- 按地址或区域分组显示待配送的订单和快递
- 支持批量标记为"配送中"或"已送达"
- 打印配送清单（可选）

### API 设计
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/delivery-plan?date=2026-06-12` | 获取指定日期的配送计划 |

### 返回结构
```json
{
  "data": {
    "orders": [...],
    "parcels": [...],
    "byAddress": {
      "幸福村三组": {
        "orders": [...],
        "parcels": [...]
      }
    }
  }
}
```

---

## 十、实现优先级

| 阶段 | 功能 | 依赖 |
|------|------|------|
| **Phase 2A** | 微信登录 + 用户认证 | 无 |
| **Phase 2A** | 收货地址簿 | 微信登录 |
| **Phase 2A** | 订阅消息 | 微信登录 |
| **Phase 2B** | 商品图片上传 | 对象存储配置 |
| **Phase 2B** | 管理端操作日志 | 无 |
| **Phase 2B** | 营收统计 + 库存预警 | 无 |
| **Phase 3A** | 微信支付 | 微信登录 + 商户号 |
| **Phase 3A** | 配送路线汇总 | 无 |
| **Phase 3A** | 快递扫码 | 无 |
| **Phase 3B** | 管理员角色权限细化 | 无 |
