from fastapi import APIRouter, Depends, HTTPException, Query
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