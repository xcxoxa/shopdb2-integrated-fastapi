from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.database import engine


router = APIRouter(
    prefix="/api/admin/policies",
    tags=["admin - policies"]
)


# 회사 정책 목록
@router.get("")
def get_policies():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM company_policies
                ORDER BY policy_id
            """)
        )

        rows = result.mappings().all()

    return {
        "count": len(rows),
        "data": [dict(row) for row in rows]
    }


# 회사 정책 상세
@router.get("/{policy_id}")
def get_policy(policy_id: int):

    with engine.connect() as connection:

        policy_result = connection.execute(
            text("""
                SELECT *
                FROM company_policies
                WHERE policy_id = :policy_id
            """),
            {
                "policy_id": policy_id
            }
        )

        policy = policy_result.mappings().first()

        if policy is None:
            raise HTTPException(
                status_code=404,
                detail="해당 회사 정책을 찾을 수 없습니다."
            )

        file_result = connection.execute(
            text("""
                SELECT *
                FROM policy_files
                WHERE policy_id = :policy_id
                ORDER BY display_order, policy_file_id
            """),
            {
                "policy_id": policy_id
            }
        )

        files = file_result.mappings().all()

    return {
        "policy": dict(policy),
        "files": [dict(row) for row in files]
    }