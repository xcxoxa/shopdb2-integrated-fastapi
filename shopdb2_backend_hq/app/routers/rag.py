from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.database import engine


router = APIRouter(
    prefix="/api/admin/rag",
    tags=["admin - RAG / AI"]
)


# AI Provider 목록
@router.get("/providers")
def get_ai_providers():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM ai_providers
                ORDER BY provider_id
            """)
        )

        rows = result.mappings().all()

    return {
        "count": len(rows),
        "data": [dict(row) for row in rows]
    }


# RAG 문서 목록
@router.get("/documents")
def get_rag_documents():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM rag_documents
                ORDER BY document_id DESC
            """)
        )

        rows = result.mappings().all()

    return {
        "count": len(rows),
        "data": [dict(row) for row in rows]
    }


# RAG 문서 상세
@router.get("/documents/{document_id}")
def get_rag_document(document_id: int):

    with engine.connect() as connection:

        document_result = connection.execute(
            text("""
                SELECT *
                FROM rag_documents
                WHERE document_id = :document_id
            """),
            {
                "document_id": document_id
            }
        )

        document = document_result.mappings().first()

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="해당 RAG 문서를 찾을 수 없습니다."
            )

        chunk_result = connection.execute(
            text("""
                SELECT *
                FROM rag_chunks
                WHERE document_id = :document_id
                ORDER BY chunk_no
            """),
            {
                "document_id": document_id
            }
        )

        chunks = chunk_result.mappings().all()

        file_result = connection.execute(
            text("""
                SELECT *
                FROM rag_document_files
                WHERE document_id = :document_id
                ORDER BY rag_document_file_id
            """),
            {
                "document_id": document_id
            }
        )

        files = file_result.mappings().all()

    return {
        "document": dict(document),
        "files": [dict(row) for row in files],
        "chunks": [dict(row) for row in chunks]
    }


# RAG 검색 기록 목록
@router.get("/query-logs")
def get_rag_query_logs():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM rag_query_logs
                ORDER BY query_log_id DESC
            """)
        )

        rows = result.mappings().all()

    return {
        "count": len(rows),
        "data": [dict(row) for row in rows]
    }


# RAG 검색 기록 상세
@router.get("/query-logs/{query_log_id}")
def get_rag_query_log(query_log_id: int):

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM rag_query_logs
                WHERE query_log_id = :query_log_id
            """),
            {
                "query_log_id": query_log_id
            }
        )

        row = result.mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="해당 RAG 검색 기록을 찾을 수 없습니다."
        )

    return dict(row)