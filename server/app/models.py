from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False, default="店主")
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="owner")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class AdminSession(Base):
    __tablename__ = "admin_sessions"

    token: Mapped[str] = mapped_column(String(128), primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    admin: Mapped[Admin] = relationship()


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="on_sale", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(80), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    receiver_name: Mapped[str] = mapped_column(String(80), nullable=False)
    receiver_phone: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    delivery_type: Mapped[str] = mapped_column(String(40), nullable=False, default="home_delivery")
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    subtotal_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    order: Mapped[Order] = relationship(back_populates="items")


class Parcel(Base):
    __tablename__ = "parcels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parcel_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    receiver_name: Mapped[str] = mapped_column(String(80), nullable=False)
    receiver_phone: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    carrier: Mapped[str] = mapped_column(String(80), nullable=False)
    tracking_no: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    pickup_code: Mapped[str] = mapped_column(String(80), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

