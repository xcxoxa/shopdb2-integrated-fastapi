import hashlib

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db


router = APIRouter(prefix="/api/customer/reviews", tags=["고객 상품 후기"])


class ReviewCreate(BaseModel):
    product_id: int = Field(gt=0)
    variant_id: int | None = Field(default=None, gt=0)
    rating: int = Field(ge=1, le=5)
    review_content: str = Field(min_length=5, max_length=2000)


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


def review_response(row) -> dict:
    return {
        "id": int(row["review_id"]),
        "productId": int(row["product_id"]),
        "variantId": int(row["variant_id"]) if row["variant_id"] is not None else None,
        "userId": int(row["user_id"]),
        "userName": row["user_name"],
        "rating": int(row["rating"]),
        "content": row["review_content"],
        "createdAt": row["created_at"].isoformat(),
        "updatedAt": row["updated_at"].isoformat(),
    }


@router.get("")
def get_product_reviews(
    product_id: int = Query(gt=0),
    db: Session = Depends(get_db),
) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT
                pr.review_id,
                pr.product_id,
                pr.variant_id,
                pr.user_id,
                u.user_name,
                pr.rating,
                pr.review_content,
                pr.created_at,
                pr.updated_at
            FROM product_reviews pr
            JOIN users u ON u.user_id = pr.user_id
            WHERE pr.product_id = :product_id
              AND EXISTS (
                  SELECT 1
                  FROM orders o
                  JOIN order_items oi ON oi.order_id = o.order_id
                  JOIN payments p ON p.order_id = o.order_id
                  WHERE o.buyer_user_id = pr.user_id
                    AND oi.product_id = pr.product_id
                    AND o.order_status IN (
                        'PAID', 'PREPARING', 'SHIPPING', 'DELIVERED', 'COMPLETED'
                    )
                    AND oi.item_status NOT IN ('CANCELLED', 'REFUNDED')
                    AND p.payment_status = 'DONE'
                    AND p.approved_at IS NOT NULL
                    AND COALESCE(p.approved_amount, 0)
                          > COALESCE(p.cancelled_amount, 0)
              )
            ORDER BY pr.created_at DESC, pr.review_id DESC
            """
        ),
        {"product_id": product_id},
    ).mappings().all()
    return [review_response(row) for row in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_product_review(
    payload: ReviewCreate,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    user_id = authenticated_user_id(authorization, db)

    purchased_item = db.execute(
        text(
            """
            SELECT oi.order_item_id, oi.variant_id
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            JOIN payments p ON p.order_id = o.order_id
            WHERE o.buyer_user_id = :user_id
              AND oi.product_id = :product_id
              AND o.order_status IN (
                  'PAID', 'PREPARING', 'SHIPPING', 'DELIVERED', 'COMPLETED'
              )
              AND oi.item_status NOT IN ('CANCELLED', 'REFUNDED')
              AND p.payment_status = 'DONE'
              AND p.approved_at IS NOT NULL
              AND COALESCE(p.approved_amount, 0)
                    > COALESCE(p.cancelled_amount, 0)
            ORDER BY p.approved_at DESC, oi.order_item_id DESC
            LIMIT 1
            """
        ),
        {"user_id": user_id, "product_id": payload.product_id},
    ).mappings().first()

    if purchased_item is None:
        raise HTTPException(
            status_code=403,
            detail="결제가 완료된 상품만 리뷰를 작성할 수 있습니다.",
        )

    duplicate = db.execute(
        text(
            """
            SELECT review_id
            FROM product_reviews
            WHERE user_id = :user_id
              AND product_id = :product_id
            LIMIT 1
            """
        ),
        {"user_id": user_id, "product_id": payload.product_id},
    ).scalar_one_or_none()
    if duplicate is not None:
        raise HTTPException(
            status_code=409,
            detail="이 상품에는 이미 리뷰를 작성했습니다.",
        )

    variant_id = payload.variant_id or purchased_item["variant_id"]
    if payload.variant_id is not None:
        bought_variant = db.execute(
            text(
                """
                SELECT 1
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.order_id
                JOIN payments p ON p.order_id = o.order_id
                WHERE o.buyer_user_id = :user_id
                  AND oi.product_id = :product_id
                  AND oi.variant_id = :variant_id
                  AND o.order_status IN (
                      'PAID', 'PREPARING', 'SHIPPING', 'DELIVERED', 'COMPLETED'
                  )
                  AND oi.item_status NOT IN ('CANCELLED', 'REFUNDED')
                  AND p.payment_status = 'DONE'
                  AND p.approved_at IS NOT NULL
                  AND COALESCE(p.approved_amount, 0)
                        > COALESCE(p.cancelled_amount, 0)
                LIMIT 1
                """
            ),
            {
                "user_id": user_id,
                "product_id": payload.product_id,
                "variant_id": payload.variant_id,
            },
        ).scalar_one_or_none()
        if bought_variant is None:
            raise HTTPException(
                status_code=403,
                detail="구매한 상품 옵션에만 리뷰를 작성할 수 있습니다.",
            )

    try:
        result = db.execute(
            text(
                """
                INSERT INTO product_reviews (
                    product_id,
                    variant_id,
                    user_id,
                    rating,
                    review_content
                ) VALUES (
                    :product_id,
                    :variant_id,
                    :user_id,
                    :rating,
                    :review_content
                )
                """
            ),
            {
                "product_id": payload.product_id,
                "variant_id": variant_id,
                "user_id": user_id,
                "rating": payload.rating,
                "review_content": payload.review_content.strip(),
            },
        )
        review_id = int(result.lastrowid)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="리뷰 데이터가 올바르지 않습니다.",
        ) from error

    row = db.execute(
        text(
            """
            SELECT
                pr.review_id,
                pr.product_id,
                pr.variant_id,
                pr.user_id,
                u.user_name,
                pr.rating,
                pr.review_content,
                pr.created_at,
                pr.updated_at
            FROM product_reviews pr
            JOIN users u ON u.user_id = pr.user_id
            WHERE pr.review_id = :review_id
            """
        ),
        {"review_id": review_id},
    ).mappings().one()
    return review_response(row)


@router.delete("/{review_id}")
def delete_product_review(
    review_id: int,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user_id = authenticated_user_id(authorization, db)
    owner_id = db.execute(
        text(
            """
            SELECT user_id
            FROM product_reviews
            WHERE review_id = :review_id
            LIMIT 1
            """
        ),
        {"review_id": review_id},
    ).scalar_one_or_none()

    if owner_id is None:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")
    if int(owner_id) != user_id:
        raise HTTPException(status_code=403, detail="본인이 작성한 리뷰만 삭제할 수 있습니다.")

    db.execute(
        text("DELETE FROM product_reviews WHERE review_id = :review_id"),
        {"review_id": review_id},
    )
    db.commit()
    return {"message": "리뷰가 삭제되었습니다."}
