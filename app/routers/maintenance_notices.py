from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.database import engine


router = APIRouter(
    prefix="/api/admin/maintenance-notices",
    tags=["admin - maintenance notices"]
)


# -----------------------------------------
# 서비스 점검 공지 목록 조회
# GET /api/admin/maintenance-notices
# -----------------------------------------
@router.get("")
def get_maintenance_notices():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM maintenance_notices
                ORDER BY maintenance_notice_id DESC
            """)
        )

        rows = result.mappings().all()

    return {
        "count": len(rows),
        "data": [dict(row) for row in rows]
    }


# -----------------------------------------
# 서비스 점검 공지 상세 조회
# GET /api/admin/maintenance-notices/{maintenance_notice_id}
# -----------------------------------------
@router.get("/{maintenance_notice_id}")
def get_maintenance_notice(maintenance_notice_id: int):

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM maintenance_notices
                WHERE maintenance_notice_id = :maintenance_notice_id
            """),
            {
                "maintenance_notice_id": maintenance_notice_id
            }
        )

        row = result.mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="해당 서비스 점검 공지를 찾을 수 없습니다."
        )

    return dict(row)