from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.database import engine


router = APIRouter(
    prefix="/api/admin/error-logs",
    tags=["admin - error logs"]
)


# -----------------------------------------
# 오류 로그 목록 조회
# GET /api/admin/error-logs
# -----------------------------------------
@router.get("")
def get_error_logs():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM error_logs
                ORDER BY error_log_id DESC
            """)
        )

        rows = result.mappings().all()

    return {
        "count": len(rows),
        "data": [dict(row) for row in rows]
    }


# -----------------------------------------
# 오류 로그 상세 조회
# GET /api/admin/error-logs/{error_log_id}
# -----------------------------------------
@router.get("/{error_log_id}")
def get_error_log(error_log_id: int):

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM error_logs
                WHERE error_log_id = :error_log_id
            """),
            {
                "error_log_id": error_log_id
            }
        )

        row = result.mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="해당 오류 로그를 찾을 수 없습니다."
        )

    return dict(row)