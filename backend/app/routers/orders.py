import re

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.buyer import (
    OrderDetailResponse,
    OrderItemResponse,
    OrderSummaryResponse,
)


router = APIRouter(
    prefix="/api/orders",
    tags=["조원 1 주문"],
)


class OrderStatusUpdateRequest(BaseModel):
    order_status: str


def read_order_statuses(db: Session) -> list[str]:
    column = db.execute(
        text("SHOW COLUMNS FROM orders LIKE 'order_status'")
    ).mappings().first()
    if column is None:
        return []
    return re.findall(r"'([^']+)'", str(column["Type"]))


ORDER_SUMMARY_QUERY = """
SELECT
    o.order_id,
    o.order_no,
    o.buyer_user_id,
    u.user_name AS buyer_name,
    ou.org_name AS organization_name,
    o.order_status,
    o.product_amount,
    o.discount_amount,
    o.shipping_amount,
    o.total_amount,
    o.ordered_at
FROM orders o
JOIN users u
    ON o.buyer_user_id = u.user_id
JOIN org_units ou
    ON o.org_id = ou.org_id
"""


@router.get("", response_model=list[OrderSummaryResponse])
def get_orders(
    buyer_user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[OrderSummaryResponse]:
    query_text = ORDER_SUMMARY_QUERY
    parameters: dict[str, int] = {}

    if buyer_user_id is not None:
        query_text += """
        WHERE o.buyer_user_id = :buyer_user_id
        """
        parameters["buyer_user_id"] = buyer_user_id

    query_text += """
    ORDER BY o.ordered_at DESC, o.order_id DESC
    """

    rows = db.execute(
        text(query_text),
        parameters,
    ).mappings().all()

    return [
        OrderSummaryResponse(**dict(row))
        for row in rows
    ]


@router.get("/statuses")
def get_order_statuses(
    db: Session = Depends(get_db),
) -> dict[str, list[str]]:
    return {"statuses": read_order_statuses(db)}


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    request: OrderStatusUpdateRequest,
    db: Session = Depends(get_db),
) -> dict:
    allowed_statuses = read_order_statuses(db)
    requested_status = request.order_status.strip().upper()

    if requested_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "사용할 수 없는 주문 상태입니다. "
                f"허용 상태: {', '.join(allowed_statuses)}"
            ),
        )

    result = db.execute(
        text(
            """
            UPDATE orders
            SET order_status = :order_status,
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = :order_id
            """
        ),
        {
            "order_id": order_id,
            "order_status": requested_status,
        },
    )

    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(404, "주문을 찾을 수 없습니다.")

    db.commit()
    return {
        "message": "주문 상태를 변경했습니다.",
        "order_id": order_id,
        "order_status": requested_status,
    }


@router.get("/{order_id}", response_model=OrderDetailResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
) -> OrderDetailResponse:
    order_query = text(
        ORDER_SUMMARY_QUERY
        + """
        WHERE o.order_id = :order_id
        """
    )

    order = db.execute(
        order_query,
        {"order_id": order_id},
    ).mappings().first()

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="주문을 찾을 수 없습니다.",
        )

    address_query = text(
        """
        SELECT
            receiver_name,
            receiver_phone,
            zipcode,
            shipping_address1,
            shipping_address2
        FROM orders
        WHERE order_id = :order_id
        """
    )

    address = db.execute(
        address_query,
        {"order_id": order_id},
    ).mappings().one()

    item_query = text(
        """
        SELECT
            oi.order_item_id,
            oi.product_id,
            oi.variant_id,
            oi.product_name_snapshot AS product_name,
            oi.sku_snapshot AS sku,
            oi.quantity,
            oi.unit_price,
            oi.item_amount,
            oi.item_status
        FROM order_items oi
        WHERE oi.order_id = :order_id
        ORDER BY oi.order_item_id
        """
    )

    item_rows = db.execute(
        item_query,
        {"order_id": order_id},
    ).mappings().all()

    return OrderDetailResponse(
        **dict(order),
        receiver_name=address["receiver_name"],
        receiver_phone=address["receiver_phone"],
        zipcode=address["zipcode"],
        shipping_address1=address["shipping_address1"],
        shipping_address2=address["shipping_address2"],
        items=[
            OrderItemResponse(**dict(item))
            for item in item_rows
        ],
    )
