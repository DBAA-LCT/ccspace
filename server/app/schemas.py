import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ProductStatus = Literal["on_sale", "off_shelf"]
OrderStatus = Literal["pending", "confirmed", "delivering", "completed", "cancelled"]
ParcelStatus = Literal["pending", "delivering", "completed", "cancelled"]
DeliveryType = Literal["home_delivery", "self_pickup"]

PHONE_RE = re.compile(r"^1[3-9]\d{9}$")


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=80)
    priceCents: int = Field(gt=0)
    originalPriceCents: int | None = Field(default=None, gt=0)
    stock: int = Field(ge=0)
    unit: str = Field(min_length=1, max_length=32)
    imageUrl: str = Field(default="", max_length=500)
    description: str = Field(default="", max_length=2000)
    status: ProductStatus = "on_sale"


class OrderItemIn(BaseModel):
    productId: int = Field(gt=0)
    quantity: int = Field(gt=0, le=999)


class OrderIn(BaseModel):
    customerName: str = Field(min_length=1, max_length=80)
    customerPhone: str = Field(min_length=1, max_length=32)
    receiverName: str = Field(min_length=1, max_length=80)
    receiverPhone: str = Field(min_length=1, max_length=32)
    address: str = Field(min_length=1, max_length=255)
    deliveryType: DeliveryType = "home_delivery"
    deliveryDate: str = Field(default="", max_length=20)
    note: str = Field(default="", max_length=500)
    items: list[OrderItemIn] = Field(min_length=1, max_length=50)
    groupId: str = Field(default="", max_length=32)

    @field_validator("customerPhone", "receiverPhone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not PHONE_RE.match(v):
            raise ValueError("手机号格式不正确")
        return v


class StatusIn(BaseModel):
    status: str = Field(min_length=1, max_length=32)


class ParcelIn(BaseModel):
    receiverName: str = Field(min_length=1, max_length=80)
    receiverPhone: str = Field(min_length=1, max_length=32)
    carrier: str = Field(min_length=1, max_length=80)
    trackingNo: str = Field(default="", max_length=120)
    pickupCode: str = Field(min_length=1, max_length=80)
    address: str = Field(min_length=1, max_length=255)
    note: str = Field(default="", max_length=500)

    @field_validator("receiverPhone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not PHONE_RE.match(v):
            raise ValueError("手机号格式不正确")
        return v


class AdminCreateIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=64)
    role: str = Field(default="staff", max_length=32)


class AdminUpdateIn(BaseModel):
    name: str | None = Field(default=None, max_length=64)
    role: str | None = Field(default=None, max_length=32)


class ChangePasswordIn(BaseModel):
    oldPassword: str = Field(min_length=1, max_length=128)
    newPassword: str = Field(min_length=6, max_length=128)


class ProductPatchIn(BaseModel):
    name: str | None = Field(default=None, max_length=160)
    category: str | None = Field(default=None, max_length=80)
    priceCents: int | None = Field(default=None, gt=0)
    originalPriceCents: int | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=32)
    imageUrl: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    status: ProductStatus | None = None


class ReviewIn(BaseModel):
    orderId: int = Field(gt=0)
    productId: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)
    content: str = Field(default="", max_length=500)


class PromotionIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    type: Literal["direct", "full_reduction"] = "direct"
    thresholdCents: int = Field(default=0, ge=0)
    discountCents: int = Field(gt=0)
    productId: int | None = None
    startAt: str
    endAt: str


class PromotionPatchIn(BaseModel):
    name: str | None = Field(default=None, max_length=160)
    isActive: bool | None = None
    endAt: str | None = None


class ReminderIn(BaseModel):
    productId: int = Field(gt=0)
    intervalDays: int = Field(default=30, ge=1, le=365)


class DeliveryPhotoIn(BaseModel):
    photoUrl: str = Field(min_length=1, max_length=500)


class SearchLogIn(BaseModel):
    keyword: str = Field(min_length=1, max_length=160)


class GroupOrderIn(BaseModel):
    customerName: str = Field(min_length=1, max_length=80)
    customerPhone: str = Field(min_length=1, max_length=32)
    receiverName: str = Field(min_length=1, max_length=80)
    receiverPhone: str = Field(min_length=1, max_length=32)
    address: str = Field(min_length=1, max_length=255)
    deliveryType: DeliveryType = "home_delivery"
    deliveryDate: str = Field(default="", max_length=20)
    note: str = Field(default="", max_length=500)
    items: list[OrderItemIn] = Field(min_length=1, max_length=50)
    groupId: str = Field(default="", max_length=32)
