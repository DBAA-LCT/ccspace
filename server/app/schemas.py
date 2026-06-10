from typing import Literal

from pydantic import BaseModel, Field


ProductStatus = Literal["on_sale", "off_shelf"]
OrderStatus = Literal["pending", "confirmed", "delivering", "completed", "cancelled"]
ParcelStatus = Literal["pending", "delivering", "completed", "cancelled"]


class LoginIn(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class ProductIn(BaseModel):
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    priceCents: int = Field(gt=0)
    stock: int = Field(ge=0)
    unit: str = Field(min_length=1)
    imageUrl: str = ""
    description: str = ""
    status: ProductStatus = "on_sale"


class OrderItemIn(BaseModel):
    productId: int = Field(gt=0)
    quantity: int = Field(gt=0)


class OrderIn(BaseModel):
    customerName: str = Field(min_length=1)
    customerPhone: str = Field(min_length=1)
    receiverName: str = Field(min_length=1)
    receiverPhone: str = Field(min_length=1)
    address: str = Field(min_length=1)
    deliveryType: str = "home_delivery"
    note: str = ""
    items: list[OrderItemIn] = Field(min_length=1)


class StatusIn(BaseModel):
    status: str


class ParcelIn(BaseModel):
    receiverName: str = Field(min_length=1)
    receiverPhone: str = Field(min_length=1)
    carrier: str = Field(min_length=1)
    trackingNo: str = ""
    pickupCode: str = Field(min_length=1)
    address: str = Field(min_length=1)
    note: str = ""

