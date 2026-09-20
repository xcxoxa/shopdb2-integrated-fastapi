import json

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.database import engine


router = APIRouter(
    prefix="/api/admin/rag",
    tags=["admin - RAG / AI"]
)


class RagEmbeddingCreate(BaseModel):
    chunk_id: int = Field(gt=0)
    embedding_provider: str = Field(min_length=1, max_length=50)
    embedding_model: str = Field(min_length=1, max_length=200)
    embedding: list[float] = Field(min_length=1)
    vector_db_type: str | None = Field(default=None, max_length=50)
    vector_collection: str | None = Field(default=None, max_length=200)
    vector_external_id: str | None = Field(default=None, max_length=500)


@router.get("/embeddings")
def get_rag_embeddings(chunk_id: int | None = Query(default=None, gt=0)):
    """RAG 문서 조각에 저장된 임베딩 정보를 조회합니다."""
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT e.embedding_id, e.chunk_id, c.document_id, c.chunk_no,
                       e.embedding_provider, e.embedding_model,
                       e.embedding_dimension, e.embedding_json,
                       e.vector_db_type, e.vector_collection,
                       e.vector_external_id, e.created_at
                FROM rag_embeddings e
                JOIN rag_chunks c ON c.chunk_id = e.chunk_id
                WHERE (:chunk_id IS NULL OR e.chunk_id = :chunk_id)
                ORDER BY e.embedding_id DESC
                """
            ),
            {"chunk_id": chunk_id},
        ).mappings().all()
    return {"count": len(rows), "data": [dict(row) for row in rows]}


@router.post("/embeddings", status_code=status.HTTP_201_CREATED)
def create_rag_embedding(data: RagEmbeddingCreate):
    """이미 계산된 임베딩 벡터를 RAG 문서 조각과 연결해 저장합니다."""
    with engine.begin() as connection:
        chunk = connection.execute(
            text("SELECT chunk_id FROM rag_chunks WHERE chunk_id = :chunk_id"),
            {"chunk_id": data.chunk_id},
        ).first()
        if chunk is None:
            raise HTTPException(status_code=404, detail="RAG 문서 조각을 찾을 수 없습니다.")

        result = connection.execute(
            text(
                """
                INSERT INTO rag_embeddings (
                    chunk_id, embedding_provider, embedding_model,
                    embedding_dimension, embedding_json, vector_db_type,
                    vector_collection, vector_external_id
                ) VALUES (
                    :chunk_id, :embedding_provider, :embedding_model,
                    :embedding_dimension, :embedding_json, :vector_db_type,
                    :vector_collection, :vector_external_id
                )
                """
            ),
            {
                "chunk_id": data.chunk_id,
                "embedding_provider": data.embedding_provider,
                "embedding_model": data.embedding_model,
                "embedding_dimension": len(data.embedding),
                "embedding_json": json.dumps(data.embedding),
                "vector_db_type": data.vector_db_type,
                "vector_collection": data.vector_collection,
                "vector_external_id": data.vector_external_id,
            },
        )
    return {
        "status": "success",
        "embedding_id": result.lastrowid,
        "embedding_dimension": len(data.embedding),
        "message": "RAG 임베딩이 저장되었습니다.",
    }


@router.delete("/embeddings/{embedding_id}")
def delete_rag_embedding(embedding_id: int):
    with engine.begin() as connection:
        result = connection.execute(
            text("DELETE FROM rag_embeddings WHERE embedding_id = :embedding_id"),
            {"embedding_id": embedding_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="RAG 임베딩을 찾을 수 없습니다.")
    return {"status": "success", "message": "RAG 임베딩이 삭제되었습니다."}


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
