from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine

# 조원 1 라우터
from app.routers.users import router as users_router
from app.routers.addresses import router as addresses_router
from app.routers.orders import router as orders_router
from app.routers.inquiries import router as inquiries_router
from app.routers.inquiry_files import router as inquiry_files_router

# 조원 2 라우터
from app.routers.categories import router as categories_router
from app.routers.sellers import router as sellers_router
from app.routers.products import router as products_router
from app.routers.inventories import router as inventories_router

# 조원 3 기존 라우터
from app.routers.org_units import router as org_units_router
from app.routers.payments import router as payments_router
from app.routers.policies import router as policies_router
from app.routers.rag import router as rag_router
from app.routers.refunds import router as refunds_router
from app.routers.refunds import admin_router as admin_refunds_router

# 조원 3 운영관리 라우터
from app.routers.audit_logs import router as audit_logs_router
from app.routers.error_logs import router as error_logs_router
from app.routers.admin_approval_requests import router as admin_approval_requests_router
from app.routers.user_notifications import router as user_notifications_router
from app.routers.maintenance_notices import router as maintenance_notices_router


app = FastAPI(
    title="SHOPDB2 통합 API",
    description="조원 1·2·3 쇼핑몰 데이터베이스 통합 API",
    version="1.0.0",
)


# 조원 1 API 연결
app.include_router(users_router)
app.include_router(addresses_router)
app.include_router(orders_router)
app.include_router(inquiries_router)
app.include_router(inquiry_files_router)

# 조원 2 API 연결
app.include_router(categories_router)
app.include_router(sellers_router)
app.include_router(products_router)
app.include_router(inventories_router)

# 조원 3 기존 API 연결
app.include_router(org_units_router)
app.include_router(payments_router)
app.include_router(policies_router)
app.include_router(rag_router)
app.include_router(refunds_router)
app.include_router(admin_refunds_router)

# 조원 3 운영관리 API 연결
app.include_router(audit_logs_router)
app.include_router(error_logs_router)
app.include_router(admin_approval_requests_router)
app.include_router(user_notifications_router)
app.include_router(maintenance_notices_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "SHOPDB2 조원 1·2·3 통합 FastAPI 서버가 실행 중입니다."
    }


@app.get("/health/db")
def database_health() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "success",
            "database": "shopdb2",
            "message": "MySQL 연결에 성공했습니다.",
        }

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=500,
            detail=f"MySQL 연결 실패: {error}",
        ) from error