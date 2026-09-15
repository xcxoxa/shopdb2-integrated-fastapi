from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.database import engine


router = APIRouter(
    prefix="/api/admin/user-notifications",
    tags=["admin - user notifications"]
)


# -----------------------------------------
# 사용자 알림 목록 조회
# GET /api/admin/user-notifications
# -----------------------------------------
@router.get("")
def get_user_notifications():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM user_notifications
                ORDER BY notification_id DESC
            """)
        )

        rows = result.mappings().all()

    return {
        "count": len(rows),
        "data": [dict(row) for row in rows]
    }


# -----------------------------------------
# 사용자 알림 상세 조회
# GET /api/admin/user-notifications/{notification_id}
# -----------------------------------------
@router.get("/{notification_id}")
def get_user_notification(notification_id: int):

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM user_notifications
                WHERE notification_id = :notification_id
            """),
            {
                "notification_id": notification_id
            }
        )

        row = result.mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="해당 사용자 알림을 찾을 수 없습니다."
        )

    return dict(row)