from datetime import datetime
import hashlib
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.customer_orders import (
    CustomerOrderCreate,
    CustomerOrderHistoryResponse,
    CustomerOrderResponse,
    CustomerPaymentConfirm,
    CustomerPaymentHistoryResponse,
    CustomerRefundRequest,
)


router = APIRouter(prefix="/api/customer/orders", tags=["고객 주문"])


def payment_provider(payment_method: str) -> str:
    return {
        "KAKAOPAY": "KAKAO",
        "TOSS": "TOSS",
        "CARD": "TOSS",
    }.get(payment_method.upper(), "TOSS")


def authenticated_user_id(
    authorization: str | None,
    db: Session,
) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    raw_token = authorization.removeprefix("Bearer ").strip()
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    user_id = db.execute(
        text(
            """
            SELECT user_id
            FROM user_sessions
            WHERE session_token_hash = :token_hash
              AND revoked_at IS NULL
              AND expires_at > CURRENT_TIMESTAMP
            LIMIT 1
            """
        ),
        {"token_hash": token_hash},
    ).scalar_one_or_none()
    if user_id is None:
        raise HTTPException(status_code=401, detail="로그인이 만료되었습니다. 다시 로그인해주세요.")
    return int(user_id)


@router.get("", response_model=list[CustomerOrderHistoryResponse])
def get_customer_orders(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> list[CustomerOrderHistoryResponse]:
    user_id = authenticated_user_id(authorization, db)
    rows = db.execute(
        text(
            """
            SELECT
                o.order_id,
                o.order_no,
                o.order_status,
                o.product_amount,
                o.shipping_amount,
                o.total_amount,
                o.ordered_at,
                (
                    SELECT rr.refund_status
                    FROM refund_requests rr
                    WHERE rr.order_id = o.order_id
                    ORDER BY rr.refund_request_id DESC
                    LIMIT 1
                ) AS refund_status,
                COUNT(oi.order_item_id) AS item_count,
                SUBSTRING_INDEX(
                    GROUP_CONCAT(
                        oi.product_name_snapshot
                        ORDER BY oi.order_item_id
                        SEPARATOR '||'
                    ),
                    '||',
                    1
                ) AS first_product_name
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            WHERE o.buyer_user_id = :user_id
            GROUP BY
                o.order_id,
                o.order_no,
                o.order_status,
                o.product_amount,
                o.shipping_amount,
                o.total_amount,
                o.ordered_at
            ORDER BY o.ordered_at DESC, o.order_id DESC
            """
        ),
        {"user_id": user_id},
    ).mappings().all()
    return [CustomerOrderHistoryResponse(**dict(row)) for row in rows]


@router.get("/payments", response_model=list[CustomerPaymentHistoryResponse])
def get_customer_payments(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> list[CustomerPaymentHistoryResponse]:
    user_id = authenticated_user_id(authorization, db)
    rows = db.execute(
        text(
            """
            SELECT
                p.payment_id,
                p.order_id,
                o.order_no,
                p.pg_provider,
                p.payment_method,
                p.payment_status,
                p.requested_amount,
                p.approved_amount,
                p.cancelled_amount,
                p.payment_key,
                p.receipt_url,
                p.requested_at,
                p.approved_at
            FROM payments p
            JOIN orders o ON o.order_id = p.order_id
            WHERE o.buyer_user_id = :user_id
            ORDER BY p.created_at DESC, p.payment_id DESC
            """
        ),
        {"user_id": user_id},
    ).mappings().all()
    return [CustomerPaymentHistoryResponse(**dict(row)) for row in rows]


@router.patch("/{order_id}/cancel")
def cancel_customer_order(
    order_id: int,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user_id = authenticated_user_id(authorization, db)
    order = db.execute(
        text(
            """
            SELECT order_id, order_status, total_amount
            FROM orders
            WHERE order_id = :order_id
              AND buyer_user_id = :user_id
            LIMIT 1
            """
        ),
        {"order_id": order_id, "user_id": user_id},
    ).mappings().first()
    if order is None:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")
    if order["order_status"] not in {"ORDERED", "PAYMENT_PENDING", "PAID"}:
        raise HTTPException(status_code=409, detail="배송이 시작된 주문은 취소할 수 없습니다.")

    stock_rows = db.execute(
        text(
            """
            SELECT variant_id, SUM(quantity) AS quantity
            FROM order_items
            WHERE order_id = :order_id AND variant_id IS NOT NULL
            GROUP BY variant_id
            """
        ),
        {"order_id": order_id},
    ).mappings().all()
    for stock_row in stock_rows:
        if order["order_status"] == "PAID":
            db.execute(
                text(
                    """
                    UPDATE inventories
                    SET stock_quantity = stock_quantity + :quantity
                    WHERE variant_id = :variant_id
                    ORDER BY inventory_id
                    LIMIT 1
                    """
                ),
                {"quantity": stock_row["quantity"], "variant_id": stock_row["variant_id"]},
            )
        else:
            db.execute(
                text(
                    """
                    UPDATE inventories
                    SET reserved_quantity = GREATEST(reserved_quantity - :quantity, 0)
                    WHERE variant_id = :variant_id
                      AND reserved_quantity >= :quantity
                    ORDER BY reserved_quantity DESC, inventory_id
                    LIMIT 1
                    """
                ),
                {"quantity": stock_row["quantity"], "variant_id": stock_row["variant_id"]},
            )

    db.execute(
        text("UPDATE orders SET order_status = 'CANCELLED' WHERE order_id = :order_id"),
        {"order_id": order_id},
    )
    db.execute(
        text("UPDATE order_items SET item_status = 'CANCELLED' WHERE order_id = :order_id"),
        {"order_id": order_id},
    )
    db.execute(
        text(
            """
            UPDATE payments
            SET payment_status = 'CANCELLED',
                cancelled_amount = requested_amount,
                balance_amount = 0,
                cancelled_at = CURRENT_TIMESTAMP
            WHERE order_id = :order_id
            """
        ),
        {"order_id": order_id},
    )
    db.commit()
    return {"message": "주문이 취소되었습니다.", "order_status": "CANCELLED"}


@router.post("/{order_id}/refund", status_code=status.HTTP_201_CREATED)
def request_customer_refund(
    order_id: int,
    payload: CustomerRefundRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str | int]:
    user_id = authenticated_user_id(authorization, db)
    order = db.execute(
        text(
            """
            SELECT order_id, total_amount, order_status
            FROM orders
            WHERE order_id = :order_id
              AND buyer_user_id = :user_id
            LIMIT 1
            """
        ),
        {"order_id": order_id, "user_id": user_id},
    ).mappings().first()
    if order is None:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")
    if order["order_status"] not in {"DELIVERED", "COMPLETED"}:
        raise HTTPException(status_code=409, detail="배송 완료된 주문만 환불을 신청할 수 있습니다.")

    duplicate = db.execute(
        text(
            """
            SELECT refund_request_id
            FROM refund_requests
            WHERE order_id = :order_id
              AND refund_status IN ('REQUESTED', 'APPROVED', 'PROCESSING')
            LIMIT 1
            """
        ),
        {"order_id": order_id},
    ).scalar_one_or_none()
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="이미 처리 중인 환불 신청이 있습니다.")

    result = db.execute(
        text(
            """
            INSERT INTO refund_requests (
                order_id, buyer_user_id, refund_policy_id,
                refund_reason, requested_amount, refund_status
            ) VALUES (
                :order_id, :user_id, NULL,
                :refund_reason, :requested_amount, 'REQUESTED'
            )
            """
        ),
        {
            "order_id": order_id,
            "user_id": user_id,
            "refund_reason": payload.refund_reason.strip(),
            "requested_amount": order["total_amount"],
        },
    )
    db.commit()
    return {
        "message": "환불 신청이 접수되었습니다.",
        "refund_request_id": int(result.lastrowid),
        "refund_status": "REQUESTED",
    }


@router.post("", response_model=CustomerOrderResponse, status_code=status.HTTP_201_CREATED)
def create_customer_order(
    payload: CustomerOrderCreate,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> CustomerOrderResponse:
    user_id = authenticated_user_id(authorization, db)
    product_amount = sum(item.unit_price * item.quantity for item in payload.items)
    shipping_amount = 0 if product_amount >= 50_000 else 3_000
    total_amount = product_amount + shipping_amount

    org_id = db.execute(
        text(
            """
            SELECT org_id
            FROM org_units
            WHERE active_yn = 'Y'
            ORDER BY CASE WHEN org_type = 'HEADQUARTER' THEN 0 ELSE 1 END, org_id
            LIMIT 1
            """
        )
    ).scalar_one_or_none()
    if org_id is None:
        raise HTTPException(status_code=500, detail="주문을 담당할 조직 정보가 없습니다.")

    order_no = f"OFFIT-{datetime.now():%Y%m%d%H%M%S%f}"
    try:
        order_result = db.execute(
            text(
                """
                INSERT INTO orders (
                    order_no, buyer_user_id, org_id, order_status,
                    product_amount, discount_amount, shipping_amount, total_amount,
                    receiver_name, receiver_phone, zipcode,
                    shipping_address1, shipping_address2
                ) VALUES (
                    :order_no, :user_id, :org_id, 'PAYMENT_PENDING',
                    :product_amount, 0, :shipping_amount, :total_amount,
                    :receiver_name, :receiver_phone, :zipcode,
                    :address1, :address2
                )
                """
            ),
            {
                "order_no": order_no,
                "user_id": user_id,
                "org_id": org_id,
                "product_amount": product_amount,
                "shipping_amount": shipping_amount,
                "total_amount": total_amount,
                "receiver_name": payload.receiver_name.strip(),
                "receiver_phone": payload.receiver_phone.strip(),
                "zipcode": payload.zipcode.strip(),
                "address1": payload.address1.strip(),
                "address2": payload.address2.strip() if payload.address2 else None,
            },
        )
        order_id = int(order_result.lastrowid)

        for item in payload.items:
            variant_sku = item.sku
            if item.variant_id is not None:
                variant = db.execute(
                    text(
                        """
                        SELECT variant_id, product_id, sku_code
                        FROM product_variants
                        WHERE variant_id = :variant_id
                          AND product_id = :product_id
                          AND active_yn = 'Y'
                        LIMIT 1
                        """
                    ),
                    {"variant_id": item.variant_id, "product_id": item.product_id},
                ).mappings().first()
                if variant is None:
                    raise HTTPException(status_code=400, detail=f"{item.product_name} 옵션이 올바르지 않습니다.")

                inventory = db.execute(
                    text(
                        """
                        SELECT inventory_id
                        FROM inventories
                        WHERE variant_id = :variant_id
                          AND stock_quantity - reserved_quantity >= :quantity
                        ORDER BY inventory_id
                        LIMIT 1
                        FOR UPDATE
                        """
                    ),
                    {"variant_id": item.variant_id, "quantity": item.quantity},
                ).scalar_one_or_none()
                if inventory is None:
                    raise HTTPException(status_code=409, detail=f"{item.product_name} 재고가 부족합니다.")
                db.execute(
                    text(
                        """
                        UPDATE inventories
                        SET reserved_quantity = reserved_quantity + :quantity
                        WHERE inventory_id = :inventory_id
                        """
                    ),
                    {"quantity": item.quantity, "inventory_id": inventory},
                )
                variant_sku = variant["sku_code"]

            db.execute(
                text(
                    """
                    INSERT INTO order_items (
                        order_id, product_id, variant_id,
                        product_name_snapshot, sku_snapshot,
                        quantity, unit_price, item_amount, item_status
                    ) VALUES (
                        :order_id, :product_id, :variant_id,
                        :product_name, :sku,
                        :quantity, :unit_price, :item_amount, 'ORDERED'
                    )
                    """
                ),
                {
                    "order_id": order_id,
                    "product_id": item.product_id,
                    "variant_id": item.variant_id,
                    "product_name": item.product_name,
                    "sku": variant_sku,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "item_amount": item.unit_price * item.quantity,
                },
            )

        payment_result = db.execute(
            text(
                """
                INSERT INTO payments (
                    order_id, pg_provider, payment_type, payment_method,
                    payment_status, requested_amount, requested_at
                ) VALUES (
                    :order_id, :pg_provider, 'NORMAL', :payment_method,
                    'READY', :total_amount, CURRENT_TIMESTAMP
                )
                """
            ),
            {
                "order_id": order_id,
                "pg_provider": payment_provider(payload.payment_method),
                "payment_method": payload.payment_method,
                "total_amount": total_amount,
            },
        )
        payment_id = int(payment_result.lastrowid)
        request_key = f"REQ-{order_id}-{secrets.token_hex(8)}"
        db.execute(
            text(
                """
                INSERT INTO payment_transactions (
                    payment_id, transaction_key, transaction_type,
                    transaction_status, transaction_amount,
                    idempotency_key, request_json
                ) VALUES (
                    :payment_id, :transaction_key, 'REQUEST',
                    'READY', :amount, :idempotency_key,
                    JSON_OBJECT('orderNo', :order_no, 'method', :payment_method, 'amount', :amount)
                )
                """
            ),
            {
                "payment_id": payment_id,
                "transaction_key": request_key,
                "amount": total_amount,
                "idempotency_key": request_key,
                "order_no": order_no,
                "payment_method": payload.payment_method,
            },
        )
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="상품 번호 또는 주문 데이터가 올바르지 않습니다.",
        ) from error

    return CustomerOrderResponse(
        order_id=order_id,
        payment_id=payment_id,
        order_no=order_no,
        order_status="PAYMENT_PENDING",
        payment_status="READY",
        product_amount=product_amount,
        shipping_amount=shipping_amount,
        total_amount=total_amount,
    )


@router.post("/{order_id}/pay")
def confirm_customer_payment(
    order_id: int,
    payload: CustomerPaymentConfirm,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str | int]:
    user_id = authenticated_user_id(authorization, db)
    row = db.execute(
        text(
            """
            SELECT o.order_id, o.order_no, o.order_status, o.total_amount,
                   p.payment_id, p.payment_status, p.payment_method
            FROM orders o
            JOIN payments p ON p.order_id = o.order_id
            WHERE o.order_id = :order_id
              AND o.buyer_user_id = :user_id
            ORDER BY p.payment_id DESC
            LIMIT 1
            """
        ),
        {"order_id": order_id, "user_id": user_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="결제할 주문을 찾을 수 없습니다.")
    if row["payment_status"] == "DONE":
        return {
            "message": "이미 결제가 완료된 주문입니다.",
            "order_id": order_id,
            "order_status": "PAID",
            "payment_status": "DONE",
        }
    if row["order_status"] != "PAYMENT_PENDING" or row["payment_status"] != "READY":
        raise HTTPException(status_code=409, detail="현재 상태에서는 결제할 수 없습니다.")

    payment_key = f"OFFIT-PAY-{order_id}-{secrets.token_hex(12)}"
    transaction_key = f"APPROVE-{order_id}-{secrets.token_hex(8)}"
    db.execute(
        text(
            """
            UPDATE payments
            SET pg_provider = :pg_provider,
                payment_key = :payment_key,
                pg_order_id = :order_no,
                customer_key = :customer_key,
                payment_method = :payment_method,
                payment_status = 'DONE',
                approved_amount = requested_amount,
                balance_amount = requested_amount,
                approved_at = CURRENT_TIMESTAMP
            WHERE payment_id = :payment_id
            """
        ),
        {
            "pg_provider": payment_provider(payload.payment_method),
            "payment_key": payment_key,
            "order_no": row["order_no"],
            "customer_key": f"CUSTOMER-{user_id}",
            "payment_method": payload.payment_method,
            "payment_id": row["payment_id"],
        },
    )
    db.execute(
        text(
            """
            INSERT INTO payment_transactions (
                payment_id, transaction_key, transaction_type,
                transaction_status, transaction_amount,
                pg_transaction_id, idempotency_key, response_json
            ) VALUES (
                :payment_id, :transaction_key, 'APPROVE',
                'SUCCESS', :amount,
                :payment_key, :idempotency_key,
                JSON_OBJECT('status', 'DONE', 'paymentKey', :payment_key, 'amount', :amount)
            )
            """
        ),
        {
            "payment_id": row["payment_id"],
            "transaction_key": transaction_key,
            "amount": row["total_amount"],
            "payment_key": payment_key,
            "idempotency_key": transaction_key,
        },
    )
    db.execute(
        text("UPDATE orders SET order_status = 'PAID' WHERE order_id = :order_id"),
        {"order_id": order_id},
    )
    db.execute(
        text("UPDATE order_items SET item_status = 'PAID' WHERE order_id = :order_id"),
        {"order_id": order_id},
    )
    stock_rows = db.execute(
        text(
            """
            SELECT variant_id, SUM(quantity) AS quantity
            FROM order_items
            WHERE order_id = :order_id AND variant_id IS NOT NULL
            GROUP BY variant_id
            """
        ),
        {"order_id": order_id},
    ).mappings().all()
    for stock_row in stock_rows:
        db.execute(
            text(
                """
                UPDATE inventories
                SET stock_quantity = GREATEST(stock_quantity - :quantity, 0),
                    reserved_quantity = GREATEST(reserved_quantity - :quantity, 0)
                WHERE variant_id = :variant_id
                  AND reserved_quantity >= :quantity
                ORDER BY reserved_quantity DESC, inventory_id
                LIMIT 1
                """
            ),
            {"quantity": stock_row["quantity"], "variant_id": stock_row["variant_id"]},
        )
    db.commit()
    return {
        "message": "결제가 완료되었습니다.",
        "order_id": order_id,
        "order_status": "PAID",
        "payment_status": "DONE",
        "payment_key": payment_key,
    }
