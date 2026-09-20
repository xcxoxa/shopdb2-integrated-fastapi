from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
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


class RefundPolicyCreate(BaseModel):
    org_id: int | None = Field(default=None, gt=0)
    policy_name: str = Field(min_length=2, max_length=200)
    allowed_days: int = Field(ge=0, le=365)
    unopened_refund_yn: Literal["Y", "N"] = "Y"
    opened_refund_yn: Literal["Y", "N"] = "N"
    defective_refund_yn: Literal["Y", "N"] = "Y"
    shipping_fee_payer: Literal["BUYER", "SELLER", "COMPANY"] = "BUYER"
    refund_policy_text: str | None = None
    effective_from: date
    effective_to: date | None = None
    active_yn: Literal["Y", "N"] = "Y"


@router.get("/policies")
def get_refund_policies(org_id: int | None = Query(default=None, gt=0)):
    """현재 적용 가능한 환불 정책을 본사 공통 정책과 지사 정책으로 조회합니다."""
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT refund_policy_id, org_id, policy_name, allowed_days,
                       unopened_refund_yn, opened_refund_yn, defective_refund_yn,
                       shipping_fee_payer, refund_policy_text,
                       effective_from, effective_to, active_yn
                FROM refund_policies
                WHERE active_yn = 'Y'
                  AND (org_id IS NULL OR org_id = :org_id)
                  AND effective_from <= CURRENT_DATE
                  AND (effective_to IS NULL OR effective_to >= CURRENT_DATE)
                ORDER BY org_id IS NULL DESC, effective_from DESC,
                         refund_policy_id DESC
                """
            ),
            {"org_id": org_id},
        ).mappings().all()
    return {"count": len(rows), "data": [dict(row) for row in rows]}


@admin_router.post("/policies", status_code=status.HTTP_201_CREATED)
def create_refund_policy(data: RefundPolicyCreate):
    """관리자가 본사 공통 또는 지사별 환불 정책을 등록합니다."""
    if data.effective_to is not None and data.effective_to < data.effective_from:
        raise HTTPException(status_code=400, detail="종료일은 시작일보다 빠를 수 없습니다.")

    with engine.begin() as connection:
        result = connection.execute(
            text(
                """
                INSERT INTO refund_policies (
                    org_id, policy_name, allowed_days, unopened_refund_yn,
                    opened_refund_yn, defective_refund_yn, shipping_fee_payer,
                    refund_policy_text, effective_from, effective_to, active_yn
                ) VALUES (
                    :org_id, :policy_name, :allowed_days, :unopened_refund_yn,
                    :opened_refund_yn, :defective_refund_yn, :shipping_fee_payer,
                    :refund_policy_text, :effective_from, :effective_to, :active_yn
                )
                """
            ),
            data.model_dump(),
        )
    return {
        "status": "success",
        "refund_policy_id": result.lastrowid,
        "message": "환불 정책이 등록되었습니다.",
    }


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
