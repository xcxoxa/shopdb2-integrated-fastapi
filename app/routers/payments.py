from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.database import engine


router = APIRouter(
    prefix="/api/admin/payments",
    tags=["admin - payments"]
)


# 결제 전체 목록 조회
@router.get("")
def get_payments():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM payments
                ORDER BY payment_id DESC
            """)
        )

        rows = result.mappings().all()

    return {
        "count": len(rows),
        "data": [dict(row) for row in rows]
    }


# 결제 상세 조회
@router.get("/{payment_id}")
def get_payment(payment_id: int):

    with engine.connect() as connection:

        payment_result = connection.execute(
            text("""
                SELECT *
                FROM payments
                WHERE payment_id = :payment_id
            """),
            {
                "payment_id": payment_id
            }
        )

        payment = payment_result.mappings().first()

        if payment is None:
            raise HTTPException(
                status_code=404,
                detail="해당 결제 정보를 찾을 수 없습니다."
            )

        transaction_result = connection.execute(
            text("""
                SELECT *
                FROM payment_transactions
                WHERE payment_id = :payment_id
                ORDER BY transaction_id
            """),
            {
                "payment_id": payment_id
            }
        )

        transactions = transaction_result.mappings().all()

        webhook_result = connection.execute(
            text("""
                SELECT *
                FROM payment_webhook_events
                WHERE payment_id = :payment_id
                ORDER BY webhook_id
            """),
            {
                "payment_id": payment_id
            }
        )

        webhooks = webhook_result.mappings().all()

    return {
        "payment": dict(payment),
        "transactions": [dict(row) for row in transactions],
        "webhook_events": [dict(row) for row in webhooks]
    }