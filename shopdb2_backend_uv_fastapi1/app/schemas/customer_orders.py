from datetime import datetime

from pydantic import BaseModel, Field


class CustomerOrderItemCreate(BaseModel):
    product_id: int
    product_name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(ge=1, le=100)
    unit_price: int = Field(ge=0)
    variant_id: int | None = None
    sku: str | None = Field(default=None, max_length=100)


class CustomerOrderCreate(BaseModel):
    receiver_name: str = Field(min_length=1, max_length=100)
    receiver_phone: str = Field(min_length=8, max_length=30)
    zipcode: str = Field(min_length=3, max_length=20)
    address1: str = Field(min_length=2, max_length=300)
    address2: str | None = Field(default=None, max_length=300)
    payment_method: str = Field(default="CARD", max_length=100)
    items: list[CustomerOrderItemCreate] = Field(min_length=1)


class CustomerRefundRequest(BaseModel):
    refund_reason: str = Field(min_length=2, max_length=1000)


class CustomerPaymentConfirm(BaseModel):
    payment_method: str = Field(default="CARD", max_length=100)


class CustomerOrderResponse(BaseModel):
    order_id: int
    payment_id: int
    order_no: str
    order_status: str
    payment_status: str
    product_amount: int
    shipping_amount: int
    total_amount: int


class CustomerOrderHistoryResponse(BaseModel):
    order_id: int
    order_no: str
    order_status: str
    product_amount: int
    shipping_amount: int
    total_amount: int
    ordered_at: datetime
    item_count: int
    first_product_name: str
    refund_status: str | None = None


class CustomerPaymentHistoryResponse(BaseModel):
    payment_id: int
    order_id: int
    order_no: str
    pg_provider: str
    payment_method: str | None = None
    payment_status: str
    requested_amount: int
    approved_amount: int
    cancelled_amount: int
    payment_key: str | None = None
    receipt_url: str | None = None
    requested_at: datetime | None = None
    approved_at: datetime | None = None
