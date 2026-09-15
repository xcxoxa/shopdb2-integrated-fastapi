from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.database import engine


router = APIRouter(
    prefix="/api/admin/audit-logs",
    tags=["admin - audit logs"]
)


# -----------------------------------------
# 감사 로그 목록 조회
# GET /api/admin/audit-logs
# -----------------------------------------
@router.get("")
def get_audit_logs():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM audit_logs
                ORDER BY audit_log_id DESC
            """)
        )

        rows = result.mappings().all()

    return {
        "count": len(rows),
        "data": [dict(row) for row in rows]
    }


# -----------------------------------------
# 감사 로그 상세 조회
# GET /api/admin/audit-logs/{audit_log_id}
# -----------------------------------------
@router.get("/{audit_log_id}")
def get_audit_log(audit_log_id: int):

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM audit_logs
                WHERE audit_log_id = :audit_log_id
            """),
            {
                "audit_log_id": audit_log_id
            }
        )

        row = result.mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="해당 감사 로그를 찾을 수 없습니다."
        )

    return dict(row)