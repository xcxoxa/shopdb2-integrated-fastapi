from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class UserResponse(BaseModel):
    user_id: int
    org_id: int | None = None
    login_id: str
    user_name: str
    email: str | None = None
    phone: str | None = None
    user_status: str
    created_at: datetime
    updated_at: datetime


class UserRoleResponse(BaseModel):
    user_id: int
    role_id: int
    role_code: str
    role_name: str


class AddressCreateRequest(BaseModel):
    address_name: str
    receiver_name: str
    receiver_phone: str
    zipcode: str
    address1: str
    address2: str | None = None
    default_yn: Literal["Y", "N"] = "N"


class AddressUpdateRequest(BaseModel):
    address_name: str
    receiver_name: str
    receiver_phone: str
    zipcode: str
    address1: str
    address2: str | None = None
    default_yn: Literal["Y", "N"] = "N"


class AddressResponse(BaseModel):
    address_id: int
    user_id: int
    address_name: str
    receiver_name: str
    receiver_phone: str
    zipcode: str
    address1: str
    address2: str | None = None
    default_yn: str
    created_at: datetime


class OrderItemResponse(BaseModel):
    order_item_id: int
    product_id: int
    variant_id: int | None = None
    product_name_snapshot: str
    sku_snapshot: str | None = None
    quantity: int
    unit_price: int
    item_amount: int
    item_status: str


class OrderSummaryResponse(BaseModel):
    order_id: int
    order_no: str
    buyer_user_id: int
    buyer_name: str
    org_id: int
    order_status: str
    product_amount: int
    discount_amount: int
    shipping_amount: int
    total_amount: int
    ordered_at: datetime
    updated_at: datetime


class OrderDetailResponse(OrderSummaryResponse):
    receiver_name: str
    receiver_phone: str
    zipcode: str
    shipping_address1: str
    shipping_address2: str | None = None
    items: list[OrderItemResponse]


InquiryType = Literal[
    "PRODUCT",
    "ORDER",
    "DELIVERY",
    "PAYMENT",
    "REFUND",
    "ETC",
]


class InquiryCreateRequest(BaseModel):
    buyer_user_id: int
    order_id: int | None = None
    inquiry_type: InquiryType = "ETC"
    inquiry_title: str
    inquiry_content: str


class InquiryResponse(BaseModel):
    inquiry_id: int
    inquiry_no: str
    buyer_user_id: int
    buyer_name: str
    order_id: int | None = None
    order_no: str | None = None
    inquiry_type: str
    inquiry_title: str
    inquiry_content: str
    inquiry_status: str
    answer_content: str | None = None
    answered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class InquiryFileCreateRequest(BaseModel):
    file_id: int
    display_order: int = 0


class InquiryFileResponse(BaseModel):
    inquiry_file_id: int
    inquiry_id: int
    file_id: int
    original_file_name: str
    mime_type: str | None = None
    file_size: int | None = None
    public_url: str | None = None
    thumbnail_url: str | None = None
    display_order: int
    created_at: datetime