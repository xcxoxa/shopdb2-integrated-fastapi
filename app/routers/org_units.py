from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.database import engine


router = APIRouter(
    prefix="/api/admin/org-units",
    tags=["admin - org_units"]
)


# --------------------------------------------------
# 조직 전체 목록 조회
# GET /api/admin/org-units
# --------------------------------------------------
@router.get("")
def get_org_units():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM org_units
                ORDER BY org_id
            """)
        )

        rows = result.mappings().all()

    return {
        "count": len(rows),
        "data": [dict(row) for row in rows]
    }


# --------------------------------------------------
# 특정 조직 1건 조회
# GET /api/admin/org-units/{org_id}
# --------------------------------------------------
@router.get("/{org_id}")
def get_org_unit(org_id: int):

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM org_units
                WHERE org_id = :org_id
            """),
            {
                "org_id": org_id
            }
        )

        row = result.mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="해당 조직을 찾을 수 없습니다."
        )

    return dict(row)