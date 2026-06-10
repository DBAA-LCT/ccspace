# 家乡小店小程序

这是一个前后端分离的乡村小店系统：外出务工的家人可以在微信小程序下单，给家里的留守老人购买日用品；小店管理员可以在 Web 管理端维护商品、处理订单、登记代收快递并安排配送。

## 技术栈

- 后端：Python + FastAPI + SQLAlchemy + MySQL
- 管理端：Vue 3 + Vite + TDesign Vue Next
- 小程序端：微信原生小程序 + TDesign Miniprogram
- 数据库：MySQL，当前连接 `119.45.182.166:9274` 的 `ccspace` 数据库

## 目录结构

```text
.
├── server/       # Python FastAPI 后端
├── admin-web/    # TDesign Vue 管理端
├── miniprogram/  # TDesign 微信小程序
└── docs/         # API 和迭代说明
```

## 后端启动

后端配置在 `server/.env`，包含 MySQL 地址、端口、账号、数据库名和管理端默认账号。

```powershell
cd D:\code\ccspace\server
.\.venv\Scripts\python.exe run.py
```

后端默认监听：

```text
http://localhost:3784
```

健康检查：

```text
http://localhost:3784/health
```

FastAPI 文档：

```text
http://localhost:3784/docs
```

## 管理端启动

```powershell
cd D:\code\ccspace\admin-web
npm run dev
```

默认 API 地址是：

```text
http://119.45.182.166:3784
```

如果本地开发要连本机后端，可以在管理端登录页修改 API 地址，或新建 `admin-web/.env`：

```text
VITE_API_BASE=http://localhost:3784
```

默认管理账号从后端 `server/.env` 读取。首次启动会自动建表并初始化管理员和示例商品。

## 小程序启动

```powershell
cd D:\code\ccspace\miniprogram
npm install
```

然后打开微信开发者工具，导入 `miniprogram` 目录，并执行“工具 / 构建 npm”。

小程序 API 地址在：

```text
miniprogram/utils/api.js
```

当前默认是：

```text
http://119.45.182.166:3784
```

正式上线微信小程序时，后端必须部署 HTTPS 域名，并在微信公众平台配置 request 合法域名；仅 IP + HTTP 适合开发联调。

## 当前功能

- 管理端登录鉴权
- 商品新增、编辑、库存维护、上下架
- 小程序商品列表、购物车、提交订单
- 订单库存扣减，取消订单自动回补库存
- 管理端订单状态流转
- 管理端快递代收登记和配送状态维护
- MySQL 自动建表和初始数据

