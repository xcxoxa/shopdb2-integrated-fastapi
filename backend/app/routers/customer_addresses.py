import hashlib

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db


router = APIRouter(prefix="/api/customer/addresses", tags=["고객 배송지"])


class CustomerAddressCreate(BaseModel):
    address_name: str = Field(min_length=1, max_length=100)
    receiver_name: str = Field(min_length=1, max_length=100)
    receiver_phone: str = Field(min_length=8, max_length=30)
    zipcode: str = Field(min_length=3, max_length=20)
    address1: str = Field(min_length=1, max_length=300)
    address2: str | None = Field(default=None, max_length=300)
    default_yn: str = Field(default="N", pattern="^[YN]$")


def authenticated_user_id(authorization: str | None, db: Session) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    raw_token = authorization.removeprefix("Bearer ").strip()
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    user_id = db.execute(
        text(
            """
            SELECT user_id
            FROM user_sessions
            WHERE session_token_hash = :token_hash
              AND revoked_at IS NULL
              AND expires_at > CURRENT_TIMESTAMP
            LIMIT 1
            """
        ),
        {"token_hash": token_hash},
    ).scalar_one_or_none()

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="로그인이 만료되었습니다. 다시 로그인해주세요.",
        )
    return int(user_id)


def get_owned_address(address_id: int, user_id: int, db: Session):
    row = db.execute(
        text(
            """
            SELECT
                address_id,
                user_id,
                address_name,
                receiver_name,
                receiver_phone,
                zipcode,
                address1,
                address2,
                default_yn,
                created_at
            FROM user_addresses
            WHERE address_id = :address_id
              AND user_id = :user_id
            LIMIT 1
            """
        ),
        {"address_id": address_id, "user_id": user_id},
    ).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="배송지를 찾을 수 없습니다.")
    return row


@router.get("")
def get_customer_addresses(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> list[dict]:
    user_id = authenticated_user_id(authorization, db)
    rows = db.execute(
        text(
            """
            SELECT
                address_id,
                user_id,
                address_name,
                receiver_name,
                receiver_phone,
                zipcode,
                address1,
                address2,
                default_yn,
                created_at
            FROM user_addresses
            WHERE user_id = :user_id
            ORDER BY
                CASE WHEN default_yn = 'Y' THEN 0 ELSE 1 END,
                address_id DESC
            """
        ),
        {"user_id": user_id},
    ).mappings().all()
    return [dict(row) for row in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_customer_address(
    payload: CustomerAddressCreate,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    user_id = authenticated_user_id(authorization, db)
    address_count = db.execute(
        text("SELECT COUNT(*) FROM user_addresses WHERE user_id = :user_id"),
        {"user_id": user_id},
    ).scalar_one()
    default_yn = "Y" if int(address_count) == 0 else payload.default_yn

    try:
        if default_yn == "Y":
            db.execute(
                text(
                    """
                    UPDATE user_addresses
                    SET default_yn = 'N'
                    WHERE user_id = :user_id
                    """
                ),
                {"user_id": user_id},
            )

        result = db.execute(
            text(
                """
                INSERT INTO user_addresses (
                    user_id,
                    address_name,
                    receiver_name,
                    receiver_phone,
                    zipcode,
                    address1,
                    address2,
                    default_yn
                ) VALUES (
                    :user_id,
                    :address_name,
                    :receiver_name,
                    :receiver_phone,
                    :zipcode,
                    :address1,
                    :address2,
                    :default_yn
                )
                """
            ),
            {
                "user_id": user_id,
                "address_name": payload.address_name.strip(),
                "receiver_name": payload.receiver_name.strip(),
                "receiver_phone": payload.receiver_phone.strip(),
                "zipcode": payload.zipcode.strip(),
                "address1": payload.address1.strip(),
                "address2": payload.address2.strip() if payload.address2 else None,
                "default_yn": default_yn,
            },
        )
        address_id = int(result.lastrowid)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=400, detail="배송지 정보가 올바르지 않습니다.") from error

    return dict(get_owned_address(address_id, user_id, db))


@router.patch("/{address_id}/default")
def set_default_customer_address(
    address_id: int,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user_id = authenticated_user_id(authorization, db)
    get_owned_address(address_id, user_id, db)

    db.execute(
        text("UPDATE user_addresses SET default_yn = 'N' WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    db.execute(
        text(
            """
            UPDATE user_addresses
            SET default_yn = 'Y'
            WHERE address_id = :address_id
              AND user_id = :user_id
            """
        ),
        {"address_id": address_id, "user_id": user_id},
    )
    db.commit()
    return {"message": "기본 배송지가 변경되었습니다."}


@router.delete("/{address_id}")
def delete_customer_address(
    address_id: int,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user_id = authenticated_user_id(authorization, db)
    address = get_owned_address(address_id, user_id, db)

    db.execute(
        text(
            """
            DELETE FROM user_addresses
            WHERE address_id = :address_id
              AND user_id = :user_id
            """
        ),
        {"address_id": address_id, "user_id": user_id},
    )

    if address["default_yn"] == "Y":
        next_address_id = db.execute(
            text(
                """
                SELECT address_id
                FROM user_addresses
                WHERE user_id = :user_id
                ORDER BY address_id
                LIMIT 1
                """
            ),
            {"user_id": user_id},
        ).scalar_one_or_none()
        if next_address_id is not None:
            db.execute(
                text(
                    """
                    UPDATE user_addresses
                    SET default_yn = 'Y'
                    WHERE address_id = :address_id
                      AND user_id = :user_id
                    """
                ),
                {"address_id": int(next_address_id), "user_id": user_id},
            )

    db.commit()
    return {"message": "배송지가 삭제되었습니다."}
