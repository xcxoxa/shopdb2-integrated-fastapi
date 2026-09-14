from decimal import Decimal
from pydantic import BaseModel


class RefundCreate(BaseModel):
    order_id: int
    buyer_user_id: int
    refund_policy_id: int | None = None
    refund_reason: str | None = None
    requested_amount: Decimal