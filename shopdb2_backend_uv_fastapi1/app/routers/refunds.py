from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.database import engine
from app.schemas.refunds import RefundCreate


# 관리자용 환불 조회 API
admin_router = APIRouter(
    prefix="/api/admin/refunds",
    tags=["admin - refunds"]
)


# 구매자용 환불 신청 API
router = APIRouter(
    prefix="/api/refunds",
    tags=["refunds"]
)


# 관리자 - 환불 목록
# GET /api/admin/refunds
@admin_router.get("")
def get_refunds():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM refund_requests
                ORDER BY refund_request_id DESC
            """)
        )

        rows = result.mappings().all()

    return {
        "count": len(rows),
        "data": [dict(row) for row in rows]
    }


# 관리자 - 환불 상세
# GET /api/admin/refunds/{refund_request_id}
@admin_router.get("/{refund_request_id}")
def get_refund(refund_request_id: int):

    with engine.connect() as connection:

        refund_result = connection.execute(
            text("""
                SELECT *
                FROM refund_requests
                WHERE refund_request_id = :refund_request_id
            """),
            {
                "refund_request_id": refund_request_id
            }
        )

        refund = refund_result.mappings().first()

        if refund is None:
            raise HTTPException(
                status_code=404,
                detail="해당 환불 신청을 찾을 수 없습니다."
            )

        item_result = connection.execute(
            text("""
                SELECT *
                FROM refund_items
                WHERE refund_request_id = :refund_request_id
                ORDER BY refund_item_id
            """),
            {
                "refund_request_id": refund_request_id
            }
        )

        items = item_result.mappings().all()

    return {
        "refund": dict(refund),
        "items": [dict(row) for row in items]
    }


# 구매자 - 환불 신청
# POST /api/refunds
@router.post(
    "",
    status_code=status.HTTP_201_CREATED
)
def create_refund(data: RefundCreate):

    with engine.begin() as connection:

        result = connection.execute(
            text("""
                INSERT INTO refund_requests (
                    order_id,
                    buyer_user_id,
                    refund_policy_id,
                    refund_reason,
                    requested_amount,
                    refund_status
                )
                VALUES (
                    :order_id,
                    :buyer_user_id,
                    :refund_policy_id,
                    :refund_reason,
                    :requested_amount,
                    'REQUESTED'
                )
            """),
            {
                "order_id": data.order_id,
                "buyer_user_id": data.buyer_user_id,
                "refund_policy_id": data.refund_policy_id,
                "refund_reason": data.refund_reason,
                "requested_amount": data.requested_amount
            }
        )

        refund_request_id = result.lastrowid

    return {
        "status": "success",
        "refund_request_id": refund_request_id,
        "message": "환불 신청이 등록되었습니다."
    }