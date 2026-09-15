from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.database import engine


router = APIRouter(
    prefix="/api/admin/approval-requests",
    tags=["admin - approval requests"]
)


# -----------------------------------------
# 관리자 승인 요청 목록 조회
# GET /api/admin/approval-requests
# -----------------------------------------
@router.get("")
def get_approval_requests():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM admin_approval_requests
                ORDER BY approval_request_id DESC
            """)
        )

        rows = result.mappings().all()

    return {
        "count": len(rows),
        "data": [dict(row) for row in rows]
    }


# -----------------------------------------
# 관리자 승인 요청 상세 조회
# GET /api/admin/approval-requests/{approval_request_id}
# -----------------------------------------
@router.get("/{approval_request_id}")
def get_approval_request(approval_request_id: int):

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM admin_approval_requests
                WHERE approval_request_id = :approval_request_id
            """),
            {
                "approval_request_id": approval_request_id
            }
        )

        row = result.mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="해당 관리자 승인 요청을 찾을 수 없습니다."
        )

    return dict(row)