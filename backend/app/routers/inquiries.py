from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.buyer import InquiryCreateRequest, InquiryResponse


router = APIRouter(
    prefix="/api/inquiries",
    tags=["조원 1 구매자 문의"],
)


INQUIRY_SELECT_QUERY = """
SELECT
    bi.inquiry_id,
    bi.inquiry_no,
    bi.buyer_user_id,
    u.user_name AS buyer_name,
    bi.order_id,
    o.order_no,
    bi.inquiry_type,
    bi.inquiry_title,
    bi.inquiry_content,
    bi.inquiry_status,
    bi.answer_content,
    bi.answered_at,
    bi.created_at,
    bi.updated_at
FROM buyer_inquiries bi
JOIN users u
    ON bi.buyer_user_id = u.user_id
LEFT JOIN orders o
    ON bi.order_id = o.order_id
"""


@router.get("", response_model=list[InquiryResponse])
def get_inquiries(
    buyer_user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[InquiryResponse]:
    query_text = INQUIRY_SELECT_QUERY
    parameters: dict[str, int] = {}

    if buyer_user_id is not None:
        query_text += """
        WHERE bi.buyer_user_id = :buyer_user_id
        """
        parameters["buyer_user_id"] = buyer_user_id

    query_text += """
    ORDER BY bi.created_at DESC, bi.inquiry_id DESC
    """

    rows = db.execute(
        text(query_text),
        parameters,
    ).mappings().all()

    return [
        InquiryResponse(**dict(row))
        for row in rows
    ]


@router.get("/{inquiry_id}", response_model=InquiryResponse)
def get_inquiry(
    inquiry_id: int,
    db: Session = Depends(get_db),
) -> InquiryResponse:
    query = text(
        INQUIRY_SELECT_QUERY
        + """
        WHERE bi.inquiry_id = :inquiry_id
        """
    )

    row = db.execute(
        query,
        {"inquiry_id": inquiry_id},
    ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="구매자 문의를 찾을 수 없습니다.",
        )

    return InquiryResponse(**dict(row))


@router.post(
    "",
    response_model=InquiryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inquiry(
    request: InquiryCreateRequest,
    db: Session = Depends(get_db),
) -> InquiryResponse:
    user_exists = db.execute(
        text(
            """
            SELECT user_id
            FROM users
            WHERE user_id = :buyer_user_id
            """
        ),
        {"buyer_user_id": request.buyer_user_id},
    ).scalar_one_or_none()

    if user_exists is None:
        raise HTTPException(
            status_code=404,
            detail="구매자를 찾을 수 없습니다.",
        )

    if request.order_id is not None:
        order_exists = db.execute(
            text(
                """
                SELECT order_id
                FROM orders
                WHERE order_id = :order_id
                AND buyer_user_id = :buyer_user_id
                """
            ),
            {
                "order_id": request.order_id,
                "buyer_user_id": request.buyer_user_id,
            },
        ).scalar_one_or_none()

        if order_exists is None:
            raise HTTPException(
                status_code=404,
                detail="해당 구매자의 주문을 찾을 수 없습니다.",
            )

    inquiry_no = (
        f"INQ-{datetime.now():%Y%m%d%H%M%S%f}"
    )

    insert_query = text(
        """
        INSERT INTO buyer_inquiries (
            inquiry_no,
            buyer_user_id,
            order_id,
            inquiry_type,
            inquiry_title,
            inquiry_content,
            inquiry_status
        )
        VALUES (
            :inquiry_no,
            :buyer_user_id,
            :order_id,
            :inquiry_type,
            :inquiry_title,
            :inquiry_content,
            'RECEIVED'
        )
        """
    )

    try:
        result = db.execute(
            insert_query,
            {
                "inquiry_no": inquiry_no,
                "buyer_user_id": request.buyer_user_id,
                "order_id": request.order_id,
                "inquiry_type": request.inquiry_type,
                "inquiry_title": request.inquiry_title,
                "inquiry_content": request.inquiry_content,
            },
        )

        inquiry_id = result.lastrowid
        db.commit()

    except IntegrityError as error:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="문의 등록에 실패했습니다.",
        ) from error

    row = db.execute(
        text(
            INQUIRY_SELECT_QUERY
            + """
            WHERE bi.inquiry_id = :inquiry_id
            """
        ),
        {"inquiry_id": inquiry_id},
    ).mappings().one()

    return InquiryResponse(**dict(row))