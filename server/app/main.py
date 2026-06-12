import logging
import re
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from .config import settings
from .database import Base, SessionLocal, engine, get_db
from .models import Admin, AdminSession, Order, OrderItem, Parcel, Product, Promotion, Reminder, Review, SearchLog
from .schemas import (
    AdminCreateIn,
    AdminUpdateIn,
    ChangePasswordIn,
    DeliveryPhotoIn,
    DeliveryType,
    GroupOrderIn,
    LoginIn,
    OrderIn,
    OrderStatus,
    ParcelIn,
    ParcelStatus,
    ProductIn,
    ProductPatchIn,
    ProductStatus,
    PromotionIn,
    PromotionPatchIn,
    ReminderIn,
    ReviewIn,
    SearchLogIn,
    StatusIn,
)
from .security import hash_password, session_token, verify_password

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("ccspace")

VALID_ORDER_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"delivering", "cancelled"},
    "delivering": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}

VALID_PARCEL_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"delivering", "cancelled"},
    "delivering": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}

_login_attempts: dict[str, list[float]] = {}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).isoformat()
    return value.isoformat()


def next_no(prefix: str, row_id: int) -> str:
    return f"{prefix}{utcnow():%Y%m%d}{row_id:06d}"


def escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def check_rate_limit(key: str, max_attempts: int, window_seconds: int = 300) -> None:
    now_ts = time.time()
    attempts = _login_attempts.get(key, [])
    attempts = [t for t in attempts if now_ts - t < window_seconds]
    if len(attempts) >= max_attempts:
        raise HTTPException(status_code=429, detail="登录尝试过于频繁，请稍后再试")
    attempts.append(now_ts)
    _login_attempts[key] = attempts


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Admin)) == 0:
            db.add(
                Admin(
                    username=settings.admin_user,
                    password_hash=hash_password(settings.admin_password),
                    name="店主",
                    role="owner",
                    created_at=utcnow(),
                )
            )
        if db.scalar(select(func.count()).select_from(Product)) == 0:
            timestamp = utcnow()
            db.add_all(
                [
                    Product(
                        name="东北珍珠米 10斤",
                        category="粮油副食",
                        price_cents=3900,
                        stock=12,
                        unit="袋",
                        image_url="https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=800&q=80",
                        description="适合家庭日常煮饭，支持送货上门。",
                        status="on_sale",
                        created_at=timestamp,
                        updated_at=timestamp,
                    ),
                    Product(
                        name="土鸡蛋 30枚",
                        category="生鲜食品",
                        price_cents=2800,
                        stock=20,
                        unit="托",
                        image_url="https://images.unsplash.com/photo-1506976785307-8732e854ad03?auto=format&fit=crop&w=800&q=80",
                        description="下单后当天或次日配送，破损可联系补送。",
                        status="on_sale",
                        created_at=timestamp,
                        updated_at=timestamp,
                    ),
                    Product(
                        name="常温纯牛奶 12盒",
                        category="饮品冲调",
                        price_cents=4800,
                        stock=9,
                        unit="箱",
                        image_url="https://images.unsplash.com/photo-1563636619-e9143da7973b?auto=format&fit=crop&w=800&q=80",
                        description="适合补充营养，整箱配送。",
                        status="on_sale",
                        created_at=timestamp,
                        updated_at=timestamp,
                    ),
                    Product(
                        name="抽纸 6包",
                        category="日用百货",
                        price_cents=1800,
                        stock=30,
                        unit="提",
                        image_url="https://images.unsplash.com/photo-1583947215259-38e31be8751f?auto=format&fit=crop&w=800&q=80",
                        description="家庭常备用纸，可和其他商品一起配送。",
                        status="on_sale",
                        created_at=timestamp,
                        updated_at=timestamp,
                    ),
                ]
            )
        db.commit()
    cleanup_expired_sessions()


def cleanup_expired_sessions() -> int:
    with SessionLocal() as db:
        count = db.query(AdminSession).filter(AdminSession.expires_at < utcnow()).delete()
        db.commit()
        if count > 0:
            logger.info("清理了 %d 个过期 session", count)
        return count


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("CCspace API 启动完成")
    yield
    logger.info("CCspace API 关闭")


app = FastAPI(title="CCspace API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    loc = first_error.get("loc", [])
    msg = first_error.get("msg", "请求参数不正确")
    field = loc[-1] if loc else ""
    detail = f"{field}: {msg}" if field else msg
    return JSONResponse(status_code=422, content={"error": detail})


def paginate(query, db: Session, page: int, page_size: int):
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return items, total


def product_out(product: Product, include_review: bool = False) -> dict:
    avg_rating = round(product.rating_sum / product.rating_count, 1) if product.rating_count > 0 else 0
    result = {
        "id": str(product.id),
        "name": product.name,
        "category": product.category,
        "priceCents": product.price_cents,
        "originalPriceCents": product.original_price_cents,
        "stock": product.stock,
        "unit": product.unit,
        "imageUrl": product.image_url,
        "description": product.description,
        "status": product.status,
        "salesCount": product.sales_count,
        "avgRating": avg_rating,
        "ratingCount": product.rating_count,
        "createdAt": iso(product.created_at),
        "updatedAt": iso(product.updated_at),
    }
    return result


def order_out(order: Order) -> dict:
    return {
        "id": str(order.id),
        "orderNo": order.order_no,
        "customerName": order.customer_name,
        "customerPhone": order.customer_phone,
        "receiverName": order.receiver_name,
        "receiverPhone": order.receiver_phone,
        "address": order.address,
        "deliveryType": order.delivery_type,
        "deliveryDate": order.delivery_date,
        "note": order.note,
        "totalCents": order.total_cents,
        "discountCents": order.discount_cents,
        "status": order.status,
        "deliveryPhoto": order.delivery_photo,
        "deliveryPhotoAt": iso(order.delivery_photo_at) if order.delivery_photo_at else None,
        "groupId": order.group_id,
        "createdAt": iso(order.created_at),
        "updatedAt": iso(order.updated_at),
        "items": [
            {
                "productId": str(item.product_id),
                "name": item.name,
                "priceCents": item.price_cents,
                "quantity": item.quantity,
                "unit": item.unit,
                "subtotalCents": item.subtotal_cents,
            }
            for item in order.items
        ],
    }


def parcel_out(parcel: Parcel) -> dict:
    return {
        "id": str(parcel.id),
        "parcelNo": parcel.parcel_no,
        "receiverName": parcel.receiver_name,
        "receiverPhone": parcel.receiver_phone,
        "carrier": parcel.carrier,
        "trackingNo": parcel.tracking_no,
        "pickupCode": parcel.pickup_code,
        "address": parcel.address,
        "note": parcel.note,
        "status": parcel.status,
        "createdAt": iso(parcel.created_at),
        "updatedAt": iso(parcel.updated_at),
    }


def admin_out(admin: Admin) -> dict:
    return {
        "id": str(admin.id),
        "username": admin.username,
        "name": admin.name,
        "role": admin.role,
        "createdAt": iso(admin.created_at),
    }


def require_admin(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> Admin:
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="请先登录管理端")
    session = db.scalar(
        select(AdminSession)
        .options(selectinload(AdminSession.admin))
        .where(AdminSession.token == token, AdminSession.expires_at > utcnow())
    )
    if not session:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return session.admin


def product_or_404(db: Session, product_id: int, lock: bool = False) -> Product:
    statement = select(Product).where(Product.id == product_id)
    if lock:
        statement = statement.with_for_update()
    product = db.scalar(statement)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return product


def order_or_404(db: Session, order_id: int, lock: bool = False) -> Order:
    statement = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    if lock:
        statement = statement.with_for_update()
    order = db.scalar(statement)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


def parcel_or_404(db: Session, parcel_id: int) -> Parcel:
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="快递不存在")
    return parcel


# ── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {"ok": True, "name": "ccspace-api"}


# ── Admin Auth ──────────────────────────────────────────────────────────────

@app.post("/api/admin/login")
def admin_login(payload: LoginIn, request: Request, db: Session = Depends(get_db)) -> dict:
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"login:{client_ip}", settings.login_rate_limit)

    admin = db.scalar(select(Admin).where(Admin.username == payload.username))
    if not admin or not verify_password(payload.password, admin.password_hash):
        logger.warning("登录失败: username=%s ip=%s", payload.username, client_ip)
        raise HTTPException(status_code=401, detail="账号或密码不正确")

    _login_attempts.pop(f"login:{client_ip}", None)

    token = session_token()
    db.add(AdminSession(
        token=token,
        admin_id=admin.id,
        expires_at=utcnow() + timedelta(hours=settings.session_ttl_hours),
        created_at=utcnow(),
    ))
    db.commit()
    logger.info("管理员登录成功: username=%s", admin.username)
    return {
        "data": {
            "token": token,
            "admin": admin_out(admin),
        }
    }


@app.post("/api/admin/logout")
def admin_logout(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
) -> dict:
    token = authorization.removeprefix("Bearer ").strip()
    db.query(AdminSession).filter(AdminSession.token == token).delete()
    db.commit()
    logger.info("管理员登出: username=%s", admin.username)
    return {"data": True}


# ── Admin Management ────────────────────────────────────────────────────────

@app.get("/api/admin/me")
def admin_me(admin: Admin = Depends(require_admin)) -> dict:
    return {"data": admin_out(admin)}


@app.post("/api/admin/change-password")
def admin_change_password(
    payload: ChangePasswordIn,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
) -> dict:
    if not verify_password(payload.oldPassword, admin.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")
    admin.password_hash = hash_password(payload.newPassword)
    db.commit()
    logger.info("管理员修改密码: username=%s", admin.username)
    return {"data": True}


@app.get("/api/admin/admins")
def list_admins(db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    if admin.role != "owner":
        raise HTTPException(status_code=403, detail="仅店主可管理管理员")
    admins = db.scalars(select(Admin).order_by(Admin.id)).all()
    return {"data": [admin_out(a) for a in admins]}


@app.post("/api/admin/admins", status_code=201)
def create_admin(
    payload: AdminCreateIn,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
) -> dict:
    if admin.role != "owner":
        raise HTTPException(status_code=403, detail="仅店主可创建管理员")
    existing = db.scalar(select(Admin).where(Admin.username == payload.username))
    if existing:
        raise HTTPException(status_code=409, detail="用户名已存在")
    new_admin = Admin(
        username=payload.username,
        password_hash=hash_password(payload.password),
        name=payload.name,
        role=payload.role,
        created_at=utcnow(),
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    logger.info("创建管理员: username=%s by=%s", payload.username, admin.username)
    return {"data": admin_out(new_admin)}


@app.put("/api/admin/admins/{admin_id}")
def update_admin(
    admin_id: int,
    payload: AdminUpdateIn,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
) -> dict:
    if admin.role != "owner":
        raise HTTPException(status_code=403, detail="仅店主可修改管理员")
    target = db.get(Admin, admin_id)
    if not target:
        raise HTTPException(status_code=404, detail="管理员不存在")
    if payload.name is not None:
        target.name = payload.name
    if payload.role is not None:
        target.role = payload.role
    db.commit()
    db.refresh(target)
    return {"data": admin_out(target)}


@app.delete("/api/admin/admins/{admin_id}")
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
) -> dict:
    if admin.role != "owner":
        raise HTTPException(status_code=403, detail="仅店主可删除管理员")
    if admin.id == admin_id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    target = db.get(Admin, admin_id)
    if not target:
        raise HTTPException(status_code=404, detail="管理员不存在")
    db.query(AdminSession).filter(AdminSession.admin_id == admin_id).delete()
    db.delete(target)
    db.commit()
    logger.info("删除管理员: username=%s by=%s", target.username, admin.username)
    return {"data": True}


# ── Public Products ─────────────────────────────────────────────────────────

@app.get("/api/products")
def list_products(
    status: ProductStatus | None = None,
    q: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    statement = select(Product)
    if status:
        statement = statement.where(Product.status == status)
    if q:
        escaped = escape_like(q)
        like = f"%{escaped}%"
        statement = statement.where(
            or_(Product.name.like(like, escape="\\"), Product.category.like(like, escape="\\"), Product.description.like(like, escape="\\"))
        )
    if category:
        statement = statement.where(Product.category == category)
    products = db.scalars(statement.order_by(Product.updated_at.desc(), Product.id.desc())).all()
    return {"data": [product_out(product) for product in products]}


@app.get("/api/products/categories")
def list_categories(db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(
        select(Product.category).where(Product.status == "on_sale").distinct().order_by(Product.category)
    ).all()
    return {"data": list(rows)}


@app.get("/api/products/hot")
def hot_products(db: Session = Depends(get_db), limit: int = Query(default=10, ge=1, le=50)) -> dict:
    products = db.scalars(
        select(Product)
        .where(Product.status == "on_sale", Product.sales_count > 0)
        .order_by(Product.sales_count.desc())
        .limit(limit)
    ).all()
    return {"data": [product_out(p) for p in products]}


@app.get("/api/products/{product_id}")
def product_detail(product_id: int, db: Session = Depends(get_db)) -> dict:
    return {"data": product_out(product_or_404(db, product_id))}


# ── Public Orders ───────────────────────────────────────────────────────────

@app.get("/api/orders")
def list_public_orders(phone: str = Query(min_length=1, max_length=32), db: Session = Depends(get_db)) -> dict:
    orders = db.scalars(
        select(Order)
        .options(selectinload(Order.items))
        .where(or_(Order.customer_phone == phone, Order.receiver_phone == phone))
        .order_by(Order.created_at.desc(), Order.id.desc())
    ).all()
    return {"data": [order_out(order) for order in orders]}


@app.post("/api/orders", status_code=201)
def create_order(payload: OrderIn, db: Session = Depends(get_db)) -> dict:
    quantities: dict[int, int] = defaultdict(int)
    for item in payload.items:
        quantities[item.productId] += item.quantity

    try:
        products: list[tuple[Product, int]] = []
        for product_id, quantity in quantities.items():
            product = product_or_404(db, product_id, lock=True)
            if product.status != "on_sale":
                raise HTTPException(status_code=409, detail=f"{product.name} 已下架")
            if product.stock < quantity:
                raise HTTPException(status_code=409, detail=f"{product.name} 库存不足（剩余 {product.stock} {product.unit}）")
            products.append((product, quantity))

        total_cents = sum(product.price_cents * quantity for product, quantity in products)
        timestamp = utcnow()
        order = Order(
            order_no="PENDING",
            customer_name=payload.customerName,
            customer_phone=payload.customerPhone,
            receiver_name=payload.receiverName,
            receiver_phone=payload.receiverPhone,
            address=payload.address,
            delivery_type=payload.deliveryType,
            delivery_date=payload.deliveryDate,
            note=payload.note,
            total_cents=total_cents,
            discount_cents=0,
            status="pending",
            delivery_photo="",
            group_id=payload.groupId,
            created_at=timestamp,
            updated_at=timestamp,
        )
        db.add(order)
        db.flush()
        order.order_no = next_no("HS", order.id)

        for product, quantity in products:
            product.stock -= quantity
            product.sales_count += quantity
            product.updated_at = timestamp
            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    name=product.name,
                    price_cents=product.price_cents,
                    quantity=quantity,
                    unit=product.unit,
                    subtotal_cents=product.price_cents * quantity,
                )
            )

        db.commit()
        db.refresh(order)
        logger.info("创建订单: order_no=%s total=%d", order.order_no, order.total_cents)
        return {"data": order_out(order)}
    except Exception:
        db.rollback()
        raise


@app.patch("/api/orders/{order_id}/cancel")
def cancel_own_order(order_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        order = order_or_404(db, order_id, lock=True)
        if order.status not in ("pending", "confirmed"):
            raise HTTPException(status_code=400, detail="该订单当前状态不可取消")
        timestamp = utcnow()
        for item in order.items:
            product = product_or_404(db, item.product_id, lock=True)
            product.stock += item.quantity
            product.updated_at = timestamp
        order.status = "cancelled"
        order.updated_at = timestamp
        db.commit()
        db.refresh(order)
        logger.info("用户取消订单: order_no=%s", order.order_no)
        return {"data": order_out(order)}
    except Exception:
        db.rollback()
        raise


# ── Admin Summary ───────────────────────────────────────────────────────────

@app.get("/api/admin/summary")
def admin_summary(db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    today_start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "data": {
            "productCount": db.scalar(select(func.count()).select_from(Product)),
            "onSaleCount": db.scalar(select(func.count()).select_from(Product).where(Product.status == "on_sale")),
            "pendingOrderCount": db.scalar(select(func.count()).select_from(Order).where(Order.status.in_(["pending", "confirmed"]))),
            "pendingParcelCount": db.scalar(select(func.count()).select_from(Parcel).where(Parcel.status.in_(["pending", "delivering"]))),
            "revenueCents": db.scalar(select(func.coalesce(func.sum(Order.total_cents), 0)).where(Order.status != "cancelled")),
            "todayOrderCount": db.scalar(select(func.count()).select_from(Order).where(Order.created_at >= today_start)),
        }
    }


# ── Admin Products ──────────────────────────────────────────────────────────

@app.get("/api/admin/products")
def admin_products(
    status: ProductStatus | None = None,
    q: str | None = None,
    category: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
) -> dict:
    statement = select(Product)
    if status:
        statement = statement.where(Product.status == status)
    if q:
        escaped = escape_like(q)
        like = f"%{escaped}%"
        statement = statement.where(
            or_(Product.name.like(like, escape="\\"), Product.category.like(like, escape="\\"), Product.description.like(like, escape="\\"))
        )
    if category:
        statement = statement.where(Product.category == category)
    statement = statement.order_by(Product.updated_at.desc(), Product.id.desc())
    items, total = paginate(statement, db, page, page_size)
    return {"data": [product_out(p) for p in items], "total": total, "page": page, "pageSize": page_size}


@app.post("/api/admin/products", status_code=201)
def admin_create_product(payload: ProductIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    timestamp = utcnow()
    product = Product(
        name=payload.name,
        category=payload.category,
        price_cents=payload.priceCents,
        original_price_cents=payload.originalPriceCents,
        stock=payload.stock,
        unit=payload.unit,
        image_url=payload.imageUrl,
        description=payload.description,
        status=payload.status,
        created_at=timestamp,
        updated_at=timestamp,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    logger.info("创建商品: name=%s admin=%s", product.name, admin.username)
    return {"data": product_out(product)}


@app.put("/api/admin/products/{product_id}")
def admin_update_product(product_id: int, payload: ProductIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    product = product_or_404(db, product_id)
    product.name = payload.name
    product.category = payload.category
    product.price_cents = payload.priceCents
    product.original_price_cents = payload.originalPriceCents
    product.stock = payload.stock
    product.unit = payload.unit
    product.image_url = payload.imageUrl
    product.description = payload.description
    product.status = payload.status
    product.updated_at = utcnow()
    db.commit()
    db.refresh(product)
    return {"data": product_out(product)}


@app.patch("/api/admin/products/{product_id}")
def admin_patch_product(product_id: int, payload: ProductPatchIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    product = product_or_404(db, product_id)
    if payload.name is not None:
        product.name = payload.name
    if payload.category is not None:
        product.category = payload.category
    if payload.priceCents is not None:
        product.price_cents = payload.priceCents
    if payload.originalPriceCents is not None:
        product.original_price_cents = payload.originalPriceCents
    if payload.stock is not None:
        product.stock = payload.stock
    if payload.unit is not None:
        product.unit = payload.unit
    if payload.imageUrl is not None:
        product.image_url = payload.imageUrl
    if payload.description is not None:
        product.description = payload.description
    if payload.status is not None:
        product.status = payload.status
    product.updated_at = utcnow()
    db.commit()
    db.refresh(product)
    return {"data": product_out(product)}


@app.patch("/api/admin/products/{product_id}/status")
def admin_update_product_status(product_id: int, payload: StatusIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    if payload.status not in ("on_sale", "off_shelf"):
        raise HTTPException(status_code=400, detail="商品状态不正确")
    product = product_or_404(db, product_id)
    product.status = payload.status
    product.updated_at = utcnow()
    db.commit()
    db.refresh(product)
    return {"data": product_out(product)}


@app.delete("/api/admin/products/{product_id}")
def admin_delete_product(product_id: int, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    product = product_or_404(db, product_id)
    has_orders = db.scalar(select(func.count()).select_from(OrderItem).where(OrderItem.product_id == product_id))
    if has_orders > 0:
        raise HTTPException(status_code=400, detail="该商品有关联订单，无法删除，请使用下架功能")
    db.delete(product)
    db.commit()
    logger.info("删除商品: name=%s admin=%s", product.name, admin.username)
    return {"data": True}


# ── Admin Orders ────────────────────────────────────────────────────────────

@app.get("/api/admin/orders")
def admin_orders(
    status: OrderStatus | None = None,
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
) -> dict:
    statement = select(Order).options(selectinload(Order.items))
    if status:
        statement = statement.where(Order.status == status)
    if q:
        escaped = escape_like(q)
        like = f"%{escaped}%"
        statement = statement.where(
            or_(
                Order.customer_name.like(like, escape="\\"),
                Order.customer_phone.like(like, escape="\\"),
                Order.receiver_name.like(like, escape="\\"),
                Order.order_no.like(like, escape="\\"),
            )
        )
    statement = statement.order_by(Order.created_at.desc(), Order.id.desc())
    items, total = paginate(statement, db, page, page_size)
    return {"data": [order_out(o) for o in items], "total": total, "page": page, "pageSize": page_size}


@app.patch("/api/admin/orders/{order_id}/status")
def admin_update_order_status(order_id: int, payload: StatusIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    if payload.status not in ("pending", "confirmed", "delivering", "completed", "cancelled"):
        raise HTTPException(status_code=400, detail="订单状态不正确")
    try:
        order = order_or_404(db, order_id, lock=True)
        allowed = VALID_ORDER_TRANSITIONS.get(order.status, set())
        if payload.status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"订单状态不能从 \"{order.status}\" 变更为 \"{payload.status}\"",
            )
        timestamp = utcnow()
        if payload.status == "cancelled" and order.status != "cancelled":
            for item in order.items:
                product = product_or_404(db, item.product_id, lock=True)
                product.stock += item.quantity
                product.updated_at = timestamp
        order.status = payload.status
        order.updated_at = timestamp
        db.commit()
        db.refresh(order)
        logger.info("订单状态变更: order_no=%s %s -> %s by=%s", order.order_no, order.status, payload.status, admin.username)
        return {"data": order_out(order)}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise


# ── Admin Parcels ───────────────────────────────────────────────────────────

@app.get("/api/admin/parcels")
def admin_parcels(
    status: ParcelStatus | None = None,
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
) -> dict:
    statement = select(Parcel)
    if status:
        statement = statement.where(Parcel.status == status)
    if q:
        escaped = escape_like(q)
        like = f"%{escaped}%"
        statement = statement.where(
            or_(
                Parcel.receiver_name.like(like, escape="\\"),
                Parcel.receiver_phone.like(like, escape="\\"),
                Parcel.parcel_no.like(like, escape="\\"),
                Parcel.tracking_no.like(like, escape="\\"),
            )
        )
    statement = statement.order_by(Parcel.created_at.desc(), Parcel.id.desc())
    items, total = paginate(statement, db, page, page_size)
    return {"data": [parcel_out(p) for p in items], "total": total, "page": page, "pageSize": page_size}


@app.post("/api/admin/parcels", status_code=201)
def admin_create_parcel(payload: ParcelIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    timestamp = utcnow()
    parcel = Parcel(
        parcel_no="PENDING",
        receiver_name=payload.receiverName,
        receiver_phone=payload.receiverPhone,
        carrier=payload.carrier,
        tracking_no=payload.trackingNo,
        pickup_code=payload.pickupCode,
        address=payload.address,
        note=payload.note,
        status="pending",
        created_at=timestamp,
        updated_at=timestamp,
    )
    db.add(parcel)
    db.flush()
    parcel.parcel_no = next_no("PK", parcel.id)
    db.commit()
    db.refresh(parcel)
    logger.info("登记快递: parcel_no=%s admin=%s", parcel.parcel_no, admin.username)
    return {"data": parcel_out(parcel)}


@app.patch("/api/admin/parcels/{parcel_id}/status")
def admin_update_parcel_status(parcel_id: int, payload: StatusIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    if payload.status not in ("pending", "delivering", "completed", "cancelled"):
        raise HTTPException(status_code=400, detail="快递状态不正确")
    parcel = parcel_or_404(db, parcel_id)
    allowed = VALID_PARCEL_TRANSITIONS.get(parcel.status, set())
    if payload.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"快递状态不能从 \"{parcel.status}\" 变更为 \"{payload.status}\"",
        )
    parcel.status = payload.status
    parcel.updated_at = utcnow()
    db.commit()
    db.refresh(parcel)
    logger.info("快递状态变更: parcel_no=%s -> %s by=%s", parcel.parcel_no, payload.status, admin.username)
    return {"data": parcel_out(parcel)}


@app.delete("/api/admin/parcels/{parcel_id}")
def admin_delete_parcel(parcel_id: int, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    parcel = parcel_or_404(db, parcel_id)
    if parcel.status not in ("pending", "cancelled"):
        raise HTTPException(status_code=400, detail="只能删除待配送或已取消的快递")
    db.delete(parcel)
    db.commit()
    logger.info("删除快递: parcel_no=%s admin=%s", parcel.parcel_no, admin.username)
    return {"data": True}


# ── 一键复购 ─────────────────────────────────────────────────────────────────

@app.get("/api/orders/{order_id}/reorder")
def reorder_items(order_id: int, db: Session = Depends(get_db)) -> dict:
    order = order_or_404(db, order_id)
    return {
        "data": [
            {
                "id": str(item.product_id),
                "productId": str(item.product_id),
                "name": item.name,
                "priceCents": item.price_cents,
                "unit": item.unit,
                "quantity": item.quantity,
            }
            for item in order.items
        ]
    }


# ── 备注模板 ─────────────────────────────────────────────────────────────────

NOTE_TEMPLATES = [
    "和快递一起送",
    "放门口就行",
    "到了打电话",
    "送到门卫处",
    "周末再送",
    "不着急，顺路送",
]


@app.get("/api/note-templates")
def get_note_templates() -> dict:
    return {"data": NOTE_TEMPLATES}


# ── 搜索 + 热门商品 ─────────────────────────────────────────────────────────

@app.post("/api/search/log")
def log_search(payload: SearchLogIn, db: Session = Depends(get_db)) -> dict:
    db.add(SearchLog(keyword=payload.keyword, source="miniprogram", created_at=utcnow()))
    db.commit()
    return {"data": True}


@app.get("/api/search/hot")
def hot_searches(db: Session = Depends(get_db), limit: int = Query(default=8, ge=1, le=20)) -> dict:
    rows = db.execute(
        select(SearchLog.keyword, func.count().label("cnt"))
        .group_by(SearchLog.keyword)
        .order_by(func.count().desc())
        .limit(limit)
    ).all()
    return {"data": [row[0] for row in rows]}


# ── 商品评价 ─────────────────────────────────────────────────────────────────

@app.post("/api/reviews", status_code=201)
def create_review(payload: ReviewIn, db: Session = Depends(get_db)) -> dict:
    order = order_or_404(db, payload.orderId)
    if order.status != "completed":
        raise HTTPException(status_code=400, detail="只能评价已完成的订单")
    existing = db.scalar(
        select(Review).where(Review.order_id == payload.orderId, Review.product_id == payload.productId)
    )
    if existing:
        raise HTTPException(status_code=409, detail="该商品已评价")
    review = Review(
        product_id=payload.productId,
        order_id=payload.orderId,
        customer_phone=order.customer_phone,
        rating=payload.rating,
        content=payload.content,
        created_at=utcnow(),
    )
    db.add(review)
    product = db.get(Product, payload.productId)
    if product:
        product.rating_sum += payload.rating
        product.rating_count += 1
    db.commit()
    db.refresh(review)
    return {"data": {"id": str(review.id), "rating": review.rating, "content": review.content}}


@app.get("/api/products/{product_id}/reviews")
def list_reviews(product_id: int, db: Session = Depends(get_db)) -> dict:
    reviews = db.scalars(
        select(Review).where(Review.product_id == product_id).order_by(Review.created_at.desc()).limit(50)
    ).all()
    return {
        "data": [
            {
                "id": str(r.id),
                "rating": r.rating,
                "content": r.content,
                "customerPhone": r.customer_phone[:3] + "****" + r.customer_phone[-4:] if len(r.customer_phone) >= 7 else "****",
                "createdAt": iso(r.created_at),
            }
            for r in reviews
        ]
    }


# ── 送达拍照 ─────────────────────────────────────────────────────────────────

@app.patch("/api/admin/orders/{order_id}/delivery-photo")
def set_delivery_photo(
    order_id: int, payload: DeliveryPhotoIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)
) -> dict:
    order = order_or_404(db, order_id)
    order.delivery_photo = payload.photoUrl
    order.delivery_photo_at = utcnow()
    order.updated_at = utcnow()
    db.commit()
    db.refresh(order)
    logger.info("上传送达照片: order_no=%s", order.order_no)
    return {"data": order_out(order)}


# ── 配送排单视图 ─────────────────────────────────────────────────────────────

@app.get("/api/admin/delivery-plan")
def delivery_plan(date: str = Query(default=""), db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    order_query = select(Order).options(selectinload(Order.items)).where(
        Order.status.in_(["confirmed", "delivering"])
    )
    parcel_query = select(Parcel).where(Parcel.status.in_(["pending", "delivering"]))

    if date:
        order_query = order_query.where(Order.delivery_date == date)

    orders = db.scalars(order_query.order_by(Order.address)).all()
    parcels = db.scalars(parcel_query.order_by(Parcel.address)).all()

    by_address: dict[str, dict] = {}
    for o in orders:
        key = o.address
        if key not in by_address:
            by_address[key] = {"orders": [], "parcels": []}
        by_address[key]["orders"].append(order_out(o))

    for p in parcels:
        key = p.address
        if key not in by_address:
            by_address[key] = {"orders": [], "parcels": []}
        by_address[key]["parcels"].append(parcel_out(p))

    return {
        "data": {
            "orders": [order_out(o) for o in orders],
            "parcels": [parcel_out(p) for p in parcels],
            "byAddress": by_address,
        }
    }


# ── 限时特价 / 满减 ─────────────────────────────────────────────────────────

@app.get("/api/promotions")
def list_active_promotions(db: Session = Depends(get_db)) -> dict:
    now = utcnow()
    promos = db.scalars(
        select(Promotion).where(Promotion.is_active == True, Promotion.start_at <= now, Promotion.end_at >= now)
    ).all()
    return {
        "data": [
            {
                "id": str(p.id),
                "name": p.name,
                "type": p.type,
                "thresholdCents": p.threshold_cents,
                "discountCents": p.discount_cents,
                "productId": str(p.product_id) if p.product_id else None,
                "startAt": iso(p.start_at),
                "endAt": iso(p.end_at),
            }
            for p in promos
        ]
    }


@app.post("/api/admin/promotions", status_code=201)
def create_promotion(payload: PromotionIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    promo = Promotion(
        name=payload.name,
        type=payload.type,
        threshold_cents=payload.thresholdCents,
        discount_cents=payload.discountCents,
        product_id=payload.productId,
        is_active=True,
        start_at=datetime.fromisoformat(payload.startAt),
        end_at=datetime.fromisoformat(payload.endAt),
        created_at=utcnow(),
    )
    db.add(promo)
    db.commit()
    db.refresh(promo)
    logger.info("创建促销: name=%s admin=%s", promo.name, admin.username)
    return {"data": {"id": str(promo.id), "name": promo.name, "type": promo.type}}


@app.get("/api/admin/promotions")
def list_all_promotions(db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    promos = db.scalars(select(Promotion).order_by(Promotion.created_at.desc())).all()
    return {
        "data": [
            {
                "id": str(p.id),
                "name": p.name,
                "type": p.type,
                "thresholdCents": p.threshold_cents,
                "discountCents": p.discount_cents,
                "productId": str(p.product_id) if p.product_id else None,
                "isActive": p.is_active,
                "startAt": iso(p.start_at),
                "endAt": iso(p.end_at),
            }
            for p in promos
        ]
    }


@app.patch("/api/admin/promotions/{promo_id}")
def update_promotion(
    promo_id: int, payload: PromotionPatchIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)
) -> dict:
    promo = db.get(Promotion, promo_id)
    if not promo:
        raise HTTPException(status_code=404, detail="促销不存在")
    if payload.name is not None:
        promo.name = payload.name
    if payload.isActive is not None:
        promo.is_active = payload.isActive
    if payload.endAt is not None:
        promo.end_at = datetime.fromisoformat(payload.endAt)
    db.commit()
    return {"data": True}


# ── 定期提醒 ─────────────────────────────────────────────────────────────────

@app.post("/api/reminders", status_code=201)
def create_reminder(payload: ReminderIn, phone: str = Query(min_length=1), db: Session = Depends(get_db)) -> dict:
    product = db.get(Product, payload.productId)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    reminder = Reminder(
        customer_phone=phone,
        product_id=payload.productId,
        interval_days=payload.intervalDays,
        next_at=utcnow() + timedelta(days=payload.intervalDays),
        is_active=True,
        created_at=utcnow(),
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return {"data": {"id": str(reminder.id), "intervalDays": reminder.interval_days}}


@app.get("/api/reminders")
def list_reminders(phone: str = Query(min_length=1), db: Session = Depends(get_db)) -> dict:
    reminders = db.scalars(
        select(Reminder).where(Reminder.customer_phone == phone, Reminder.is_active == True)
    ).all()
    result = []
    for r in reminders:
        product = db.get(Product, r.product_id)
        result.append({
            "id": str(r.id),
            "productId": str(r.product_id),
            "productName": product.name if product else "未知商品",
            "intervalDays": r.interval_days,
            "nextAt": iso(r.next_at),
        })
    return {"data": result}


@app.delete("/api/reminders/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)) -> dict:
    reminder = db.get(Reminder, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="提醒不存在")
    reminder.is_active = False
    db.commit()
    return {"data": True}


# ── 账单月报 ─────────────────────────────────────────────────────────────────

@app.get("/api/stats/monthly")
def monthly_stats(phone: str = Query(min_length=1), db: Session = Depends(get_db)) -> dict:
    orders = db.scalars(
        select(Order).where(
            or_(Order.customer_phone == phone, Order.receiver_phone == phone),
            Order.status != "cancelled",
        ).order_by(Order.created_at.desc())
    ).all()

    months: dict[str, dict] = {}
    for o in orders:
        key = o.created_at.strftime("%Y-%m")
        if key not in months:
            months[key] = {"month": key, "orderCount": 0, "totalCents": 0, "itemCount": 0}
        months[key]["orderCount"] += 1
        months[key]["totalCents"] += o.total_cents
        months[key]["itemCount"] += sum(i.quantity for i in o.items)

    return {"data": list(months.values())[:12]}


# ── 拼单 ─────────────────────────────────────────────────────────────────────

@app.get("/api/group-orders/{group_id}")
def get_group_order(group_id: str, db: Session = Depends(get_db)) -> dict:
    orders = db.scalars(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.group_id == group_id)
        .order_by(Order.created_at)
    ).all()
    if not orders:
        raise HTTPException(status_code=404, detail="拼单不存在")
    total_cents = sum(o.total_cents for o in orders)
    return {
        "data": {
            "groupId": group_id,
            "orderCount": len(orders),
            "totalCents": total_cents,
            "orders": [order_out(o) for o in orders],
        }
    }
