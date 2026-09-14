from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.buyer import (
    InquiryFileCreateRequest,
    InquiryFileResponse,
)


router = APIRouter(
    prefix="/api",
    tags=["조원 1 문의 첨부파일"],
)


def find_inquiry_file(
    inquiry_file_id: int,
    db: Session,
) -> dict:
    inquiry_file = db.execute(
        text(
            """
            SELECT
                inf.inquiry_file_id,
                inf.inquiry_id,
                inf.file_id,
                fa.original_file_name,
                fa.mime_type,
                fa.file_size,
                fa.public_url,
                fa.thumbnail_url,
                inf.display_order,
                inf.created_at
            FROM inquiry_files AS inf
            INNER JOIN file_assets AS fa
                ON fa.file_id = inf.file_id
            WHERE inf.inquiry_file_id = :inquiry_file_id
            """
        ),
        {"inquiry_file_id": inquiry_file_id},
    ).mappings().first()

    if inquiry_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문의 첨부파일을 찾을 수 없습니다.",
        )

    return dict(inquiry_file)


@router.get(
    "/inquiries/{inquiry_id}/files",
    response_model=list[InquiryFileResponse],
)
def get_inquiry_files(
    inquiry_id: int,
    db: Session = Depends(get_db),
) -> list[dict]:
    inquiry = db.execute(
        text(
            """
            SELECT inquiry_id
            FROM buyer_inquiries
            WHERE inquiry_id = :inquiry_id
            """
        ),
        {"inquiry_id": inquiry_id},
    ).first()

    if inquiry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="구매자 문의를 찾을 수 없습니다.",
        )

    inquiry_files = db.execute(
        text(
            """
            SELECT
                inf.inquiry_file_id,
                inf.inquiry_id,
                inf.file_id,
                fa.original_file_name,
                fa.mime_type,
                fa.file_size,
                fa.public_url,
                fa.thumbnail_url,
                inf.display_order,
                inf.created_at
            FROM inquiry_files AS inf
            INNER JOIN file_assets AS fa
                ON fa.file_id = inf.file_id
            WHERE inf.inquiry_id = :inquiry_id
            ORDER BY
                inf.display_order,
                inf.inquiry_file_id
            """
        ),
        {"inquiry_id": inquiry_id},
    ).mappings().all()

    return [dict(inquiry_file) for inquiry_file in inquiry_files]


@router.post(
    "/inquiries/{inquiry_id}/files",
    response_model=InquiryFileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inquiry_file(
    inquiry_id: int,
    request: InquiryFileCreateRequest,
    db: Session = Depends(get_db),
) -> dict:
    inquiry = db.execute(
        text(
            """
            SELECT inquiry_id
            FROM buyer_inquiries
            WHERE inquiry_id = :inquiry_id
            """
        ),
        {"inquiry_id": inquiry_id},
    ).first()

    if inquiry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="구매자 문의를 찾을 수 없습니다.",
        )

    file_asset = db.execute(
        text(
            """
            SELECT file_id
            FROM file_assets
            WHERE file_id = :file_id
            """
        ),
        {"file_id": request.file_id},
    ).first()

    if file_asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일 정보를 찾을 수 없습니다.",
        )

    duplicate = db.execute(
        text(
            """
            SELECT inquiry_file_id
            FROM inquiry_files
            WHERE inquiry_id = :inquiry_id
              AND file_id = :file_id
            """
        ),
        {
            "inquiry_id": inquiry_id,
            "file_id": request.file_id,
        },
    ).first()

    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 문의에 연결된 파일입니다.",
        )

    result = db.execute(
        text(
            """
            INSERT INTO inquiry_files (
                inquiry_id,
                file_id,
                display_order
            )
            VALUES (
                :inquiry_id,
                :file_id,
                :display_order
            )
            """
        ),
        {
            "inquiry_id": inquiry_id,
            "file_id": request.file_id,
            "display_order": request.display_order,
        },
    )

    db.commit()

    return find_inquiry_file(result.lastrowid, db)


@router.delete(
    "/inquiries/{inquiry_id}/files/{inquiry_file_id}",
    status_code=status.HTTP_200_OK,
)
def delete_inquiry_file(
    inquiry_id: int,
    inquiry_file_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    inquiry_file = db.execute(
        text(
            """
            SELECT inquiry_file_id
            FROM inquiry_files
            WHERE inquiry_file_id = :inquiry_file_id
              AND inquiry_id = :inquiry_id
            """
        ),
        {
            "inquiry_file_id": inquiry_file_id,
            "inquiry_id": inquiry_id,
        },
    ).first()

    if inquiry_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문의에 연결된 첨부파일을 찾을 수 없습니다.",
        )

    db.execute(
        text(
            """
            DELETE FROM inquiry_files
            WHERE inquiry_file_id = :inquiry_file_id
              AND inquiry_id = :inquiry_id
            """
        ),
        {
            "inquiry_file_id": inquiry_file_id,
            "inquiry_id": inquiry_id,
        },
    )

    db.commit()

    return {
        "message": "문의 첨부파일 연결이 삭제되었습니다."
    }