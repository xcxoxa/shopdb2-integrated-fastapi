from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.buyer import UserResponse, UserRoleResponse


router = APIRouter(
    prefix="/api/users",
    tags=["조원 1 회원 및 권한"],
)


@router.get("", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)) -> list[UserResponse]:
    query = text(
        """
        SELECT
            u.user_id,
            u.login_id,
            u.user_name,
            u.email,
            u.phone,
            u.user_status,
            u.created_at,
            GROUP_CONCAT(
                r.role_code
                ORDER BY r.role_id
                SEPARATOR ','
            ) AS role_codes
        FROM users u
        LEFT JOIN user_roles ur
            ON u.user_id = ur.user_id
        LEFT JOIN roles r
            ON ur.role_id = r.role_id
        GROUP BY
            u.user_id,
            u.login_id,
            u.user_name,
            u.email,
            u.phone,
            u.user_status,
            u.created_at
        ORDER BY u.user_id
        """
    )

    rows = db.execute(query).mappings().all()

    return [
        UserResponse(
            user_id=row["user_id"],
            login_id=row["login_id"],
            user_name=row["user_name"],
            email=row["email"],
            phone=row["phone"],
            user_status=row["user_status"],
            created_at=row["created_at"],
            roles=(
                row["role_codes"].split(",")
                if row["role_codes"]
                else []
            ),
        )
        for row in rows
    ]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
) -> UserResponse:
    query = text(
        """
        SELECT
            u.user_id,
            u.login_id,
            u.user_name,
            u.email,
            u.phone,
            u.user_status,
            u.created_at,
            GROUP_CONCAT(
                r.role_code
                ORDER BY r.role_id
                SEPARATOR ','
            ) AS role_codes
        FROM users u
        LEFT JOIN user_roles ur
            ON u.user_id = ur.user_id
        LEFT JOIN roles r
            ON ur.role_id = r.role_id
        WHERE u.user_id = :user_id
        GROUP BY
            u.user_id,
            u.login_id,
            u.user_name,
            u.email,
            u.phone,
            u.user_status,
            u.created_at
        """
    )

    row = db.execute(
        query,
        {"user_id": user_id},
    ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="회원을 찾을 수 없습니다.",
        )

    return UserResponse(
        user_id=row["user_id"],
        login_id=row["login_id"],
        user_name=row["user_name"],
        email=row["email"],
        phone=row["phone"],
        user_status=row["user_status"],
        created_at=row["created_at"],
        roles=(
            row["role_codes"].split(",")
            if row["role_codes"]
            else []
        ),
    )


@router.get("/{user_id}/roles", response_model=UserRoleResponse)
def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
) -> UserRoleResponse:
    query = text(
        """
        SELECT
            u.user_id,
            u.login_id,
            u.user_name,
            GROUP_CONCAT(
                r.role_code
                ORDER BY r.role_id
                SEPARATOR ','
            ) AS role_codes
        FROM users u
        LEFT JOIN user_roles ur
            ON u.user_id = ur.user_id
        LEFT JOIN roles r
            ON ur.role_id = r.role_id
        WHERE u.user_id = :user_id
        GROUP BY
            u.user_id,
            u.login_id,
            u.user_name
        """
    )

    row = db.execute(
        query,
        {"user_id": user_id},
    ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="회원을 찾을 수 없습니다.",
        )

    return UserRoleResponse(
        user_id=row["user_id"],
        login_id=row["login_id"],
        user_name=row["user_name"],
        roles=(
            row["role_codes"].split(",")
            if row["role_codes"]
            else []
        ),
    )