from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from .config import settings
from .database import Base, SessionLocal, engine, get_db
from .models import Admin, AdminSession, Order, OrderItem, Parcel, Product
from .schemas import (
    LoginIn,
    OrderIn,
    OrderStatus,
    ParcelIn,
    ParcelStatus,
    ProductIn,
    ProductStatus,
    StatusIn,
)
from .security import hash_password, session_token, verify_password


app = FastAPI(title="Home Shop API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    message = first_error.get("msg", "请求参数不正确")
    return JSONResponse(status_code=422, content={"error": message})


def now() -> datetime:
    return datetime.utcnow()


def iso(value: datetime) -> str:
    return value.isoformat() + "Z"


def next_no(prefix: str, row_id: int) -> str:
    return f"{prefix}{now():%Y%m%d}{row_id:04d}"


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Admin)) == 0:
            db.add(
                Admin(
                    username=settings.admin_user,
                    password_hash=hash_password(settings.admin_password),
                    name="\u5e97\u4e3b",
                    role="owner",
                    created_at=now(),
                )
            )
        if db.scalar(select(func.count()).select_from(Product)) == 0:
            timestamp = now()
            db.add_all(
                [
                    Product(
                        name="\u4e1c\u5317\u73cd\u73e0\u7c73 10\u65a4",
                        category="\u7cae\u6cb9\u526f\u98df",
                        price_cents=3900,
                        stock=12,
                        unit="\u888b",
                        image_url="https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=800&q=80",
                        description="\u9002\u5408\u5bb6\u5ead\u65e5\u5e38\u716e\u996d\uff0c\u652f\u6301\u9001\u5230\u6751\u91cc\u8001\u4eba\u5bb6\u4e2d\u3002",
                        status="on_sale",
                        created_at=timestamp,
                        updated_at=timestamp,
                    ),
                    Product(
                        name="\u571f\u9e21\u86cb 30\u679a",
                        category="\u751f\u9c9c\u98df\u54c1",
                        price_cents=2800,
                        stock=20,
                        unit="\u6258",
                        image_url="https://images.unsplash.com/photo-1506976785307-8732e854ad03?auto=format&fit=crop&w=800&q=80",
                        description="\u4e0b\u5355\u540e\u5f53\u5929\u6216\u6b21\u65e5\u914d\u9001\uff0c\u7834\u635f\u53ef\u8054\u7cfb\u8865\u9001\u3002",
                        status="on_sale",
                        created_at=timestamp,
                        updated_at=timestamp,
                    ),
                    Product(
                        name="\u5e38\u6e29\u7eaf\u725b\u5976 12\u76d2",
                        category="\u996e\u54c1\u51b2\u8c03",
                        price_cents=4800,
                        stock=9,
                        unit="\u7bb1",
                        image_url="https://images.unsplash.com/photo-1563636619-e9143da7973b?auto=format&fit=crop&w=800&q=80",
                        description="\u9002\u5408\u7ed9\u8001\u4eba\u8865\u5145\u8425\u517b\uff0c\u6574\u7bb1\u914d\u9001\u3002",
                        status="on_sale",
                        created_at=timestamp,
                        updated_at=timestamp,
                    ),
                    Product(
                        name="\u62bd\u7eb8 6\u5305",
                        category="\u65e5\u7528\u767e\u8d27",
                        price_cents=1800,
                        stock=30,
                        unit="\u63d0",
                        image_url="https://images.unsplash.com/photo-1583947215259-38e31be8751f?auto=format&fit=crop&w=800&q=80",
                        description="\u5bb6\u5ead\u5e38\u5907\u7528\u7eb8\uff0c\u53ef\u548c\u5176\u4ed6\u5546\u54c1\u4e00\u8d77\u914d\u9001\u3002",
                        status="on_sale",
                        created_at=timestamp,
                        updated_at=timestamp,
                    ),
                ]
            )
        db.commit()


@app.on_event("startup")
def startup() -> None:
    init_db()


def product_out(product: Product) -> dict:
    return {
        "id": str(product.id),
        "name": product.name,
        "category": product.category,
        "priceCents": product.price_cents,
        "stock": product.stock,
        "unit": product.unit,
        "imageUrl": product.image_url,
        "description": product.description,
        "status": product.status,
        "createdAt": iso(product.created_at),
        "updatedAt": iso(product.updated_at),
    }


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
        "note": order.note,
        "totalCents": order.total_cents,
        "status": order.status,
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


def require_admin(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> Admin:
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="请先登录管理端")
    session = db.scalar(
        select(AdminSession)
        .options(selectinload(AdminSession.admin))
        .where(AdminSession.token == token, AdminSession.expires_at > now())
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


@app.get("/health")
def health() -> dict:
    return {"ok": True, "name": "home-shop-api", "database": settings.safe_database_url}


@app.post("/api/admin/login")
def admin_login(payload: LoginIn, db: Session = Depends(get_db)) -> dict:
    admin = db.scalar(select(Admin).where(Admin.username == payload.username))
    if not admin or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码不正确")

    token = session_token()
    db.add(AdminSession(token=token, admin_id=admin.id, expires_at=now() + timedelta(days=1), created_at=now()))
    db.commit()
    return {
        "data": {
            "token": token,
            "admin": {
                "id": str(admin.id),
                "username": admin.username,
                "name": admin.name,
                "role": admin.role,
            },
        }
    }


@app.post("/api/admin/logout")
def admin_logout(authorization: str = Header(default=""), db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    token = authorization.removeprefix("Bearer ").strip()
    db.query(AdminSession).filter(AdminSession.token == token).delete()
    db.commit()
    return {"data": True}


@app.get("/api/products")
def list_products(
    status: ProductStatus | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    statement = select(Product)
    if status:
        statement = statement.where(Product.status == status)
    if q:
        like = f"%{q}%"
        statement = statement.where(or_(Product.name.like(like), Product.category.like(like), Product.description.like(like)))
    products = db.scalars(statement.order_by(Product.updated_at.desc(), Product.id.desc())).all()
    return {"data": [product_out(product) for product in products]}


@app.get("/api/products/{product_id}")
def product_detail(product_id: int, db: Session = Depends(get_db)) -> dict:
    return {"data": product_out(product_or_404(db, product_id))}


@app.get("/api/orders")
def list_public_orders(phone: str = Query(min_length=1), db: Session = Depends(get_db)) -> dict:
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
                raise HTTPException(status_code=409, detail=f"{product.name} 库存不足")
            products.append((product, quantity))

        total_cents = sum(product.price_cents * quantity for product, quantity in products)
        timestamp = now()
        order = Order(
            order_no="PENDING",
            customer_name=payload.customerName,
            customer_phone=payload.customerPhone,
            receiver_name=payload.receiverName,
            receiver_phone=payload.receiverPhone,
            address=payload.address,
            delivery_type=payload.deliveryType,
            note=payload.note,
            total_cents=total_cents,
            status="pending",
            created_at=timestamp,
            updated_at=timestamp,
        )
        db.add(order)
        db.flush()
        order.order_no = next_no("HS", order.id)

        for product, quantity in products:
            product.stock -= quantity
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
        return {"data": order_out(order_or_404(db, order.id))}
    except Exception:
        db.rollback()
        raise


@app.get("/api/admin/summary")
def admin_summary(db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    return {
        "data": {
            "productCount": db.scalar(select(func.count()).select_from(Product)),
            "onSaleCount": db.scalar(select(func.count()).select_from(Product).where(Product.status == "on_sale")),
            "pendingOrderCount": db.scalar(select(func.count()).select_from(Order).where(Order.status.in_(["pending", "confirmed"]))),
            "pendingParcelCount": db.scalar(select(func.count()).select_from(Parcel).where(Parcel.status.in_(["pending", "delivering"]))),
            "revenueCents": db.scalar(select(func.coalesce(func.sum(Order.total_cents), 0)).where(Order.status != "cancelled")),
        }
    }


@app.get("/api/admin/products")
def admin_products(status: ProductStatus | None = None, q: str | None = None, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    return list_products(status=status, q=q, db=db)


@app.post("/api/admin/products", status_code=201)
def admin_create_product(payload: ProductIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    timestamp = now()
    product = Product(
        name=payload.name,
        category=payload.category,
        price_cents=payload.priceCents,
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
    return {"data": product_out(product)}


@app.put("/api/admin/products/{product_id}")
def admin_update_product(product_id: int, payload: ProductIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    product = product_or_404(db, product_id)
    product.name = payload.name
    product.category = payload.category
    product.price_cents = payload.priceCents
    product.stock = payload.stock
    product.unit = payload.unit
    product.image_url = payload.imageUrl
    product.description = payload.description
    product.status = payload.status
    product.updated_at = now()
    db.commit()
    db.refresh(product)
    return {"data": product_out(product)}


@app.patch("/api/admin/products/{product_id}/status")
def admin_update_product_status(product_id: int, payload: StatusIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    if payload.status not in ("on_sale", "off_shelf"):
        raise HTTPException(status_code=400, detail="商品状态不正确")
    product = product_or_404(db, product_id)
    product.status = payload.status
    product.updated_at = now()
    db.commit()
    db.refresh(product)
    return {"data": product_out(product)}


@app.get("/api/admin/orders")
def admin_orders(status: OrderStatus | None = None, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    statement = select(Order).options(selectinload(Order.items))
    if status:
        statement = statement.where(Order.status == status)
    orders = db.scalars(statement.order_by(Order.created_at.desc(), Order.id.desc())).all()
    return {"data": [order_out(order) for order in orders]}


@app.patch("/api/admin/orders/{order_id}/status")
def admin_update_order_status(order_id: int, payload: StatusIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    if payload.status not in ("pending", "confirmed", "delivering", "completed", "cancelled"):
        raise HTTPException(status_code=400, detail="订单状态不正确")
    try:
        order = order_or_404(db, order_id, lock=True)
        timestamp = now()
        if payload.status == "cancelled" and order.status != "cancelled":
            for item in order.items:
                product = product_or_404(db, item.product_id, lock=True)
                product.stock += item.quantity
                product.updated_at = timestamp
        order.status = payload.status
        order.updated_at = timestamp
        db.commit()
        return {"data": order_out(order_or_404(db, order_id))}
    except Exception:
        db.rollback()
        raise


@app.get("/api/admin/parcels")
def admin_parcels(status: ParcelStatus | None = None, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    statement = select(Parcel)
    if status:
        statement = statement.where(Parcel.status == status)
    parcels = db.scalars(statement.order_by(Parcel.created_at.desc(), Parcel.id.desc())).all()
    return {"data": [parcel_out(parcel) for parcel in parcels]}


@app.post("/api/admin/parcels", status_code=201)
def admin_create_parcel(payload: ParcelIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    timestamp = now()
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
    return {"data": parcel_out(parcel)}


@app.patch("/api/admin/parcels/{parcel_id}/status")
def admin_update_parcel_status(parcel_id: int, payload: StatusIn, db: Session = Depends(get_db), admin: Admin = Depends(require_admin)) -> dict:
    if payload.status not in ("pending", "delivering", "completed", "cancelled"):
        raise HTTPException(status_code=400, detail="快递状态不正确")
    parcel = parcel_or_404(db, parcel_id)
    parcel.status = payload.status
    parcel.updated_at = now()
    db.commit()
    db.refresh(parcel)
    return {"data": parcel_out(parcel)}
