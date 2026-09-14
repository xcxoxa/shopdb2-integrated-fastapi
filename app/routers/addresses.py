from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.buyer import (
    AddressCreateRequest,
    AddressResponse,
    AddressUpdateRequest,
)


router = APIRouter(
    prefix="/api",
    tags=["조원 1 배송지"],
)


def find_address(address_id: int, db: Session) -> dict:
    address = db.execute(
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
            """
        ),
        {"address_id": address_id},
    ).mappings().first()

    if address is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="배송지를 찾을 수 없습니다.",
        )

    return dict(address)


@router.get(
    "/users/{user_id}/addresses",
    response_model=list[AddressResponse],
)
def get_user_addresses(
    user_id: int,
    db: Session = Depends(get_db),
) -> list[dict]:
    user = db.execute(
        text(
            """
            SELECT user_id
            FROM users
            WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    addresses = db.execute(
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
                address_id
            """
        ),
        {"user_id": user_id},
    ).mappings().all()

    return [dict(address) for address in addresses]


@router.post(
    "/users/{user_id}/addresses",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_address(
    user_id: int,
    request: AddressCreateRequest,
    db: Session = Depends(get_db),
) -> dict:
    user = db.execute(
        text(
            """
            SELECT user_id
            FROM users
            WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    if request.default_yn == "Y":
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
            )
            VALUES (
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
            "address_name": request.address_name,
            "receiver_name": request.receiver_name,
            "receiver_phone": request.receiver_phone,
            "zipcode": request.zipcode,
            "address1": request.address1,
            "address2": request.address2,
            "default_yn": request.default_yn,
        },
    )

    db.commit()

    return find_address(result.lastrowid, db)


@router.put(
    "/addresses/{address_id}",
    response_model=AddressResponse,
)
def update_address(
    address_id: int,
    request: AddressUpdateRequest,
    db: Session = Depends(get_db),
) -> dict:
    current_address = find_address(address_id, db)
    user_id = current_address["user_id"]

    if request.default_yn == "Y":
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

    db.execute(
        text(
            """
            UPDATE user_addresses
            SET
                address_name = :address_name,
                receiver_name = :receiver_name,
                receiver_phone = :receiver_phone,
                zipcode = :zipcode,
                address1 = :address1,
                address2 = :address2,
                default_yn = :default_yn
            WHERE address_id = :address_id
            """
        ),
        {
            "address_id": address_id,
            "address_name": request.address_name,
            "receiver_name": request.receiver_name,
            "receiver_phone": request.receiver_phone,
            "zipcode": request.zipcode,
            "address1": request.address1,
            "address2": request.address2,
            "default_yn": request.default_yn,
        },
    )

    db.commit()

    return find_address(address_id, db)


@router.delete(
    "/addresses/{address_id}",
    status_code=status.HTTP_200_OK,
)
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    find_address(address_id, db)

    db.execute(
        text(
            """
            DELETE FROM user_addresses
            WHERE address_id = :address_id
            """
        ),
        {"address_id": address_id},
    )

    db.commit()

    return {"message": "배송지가 삭제되었습니다."}