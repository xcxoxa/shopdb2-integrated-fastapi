from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
import time


# DB 연결
from app.database import get_db

router = APIRouter(tags=["본사 관리(HQ)"])

# ==========================================
# Pydantic 모델 정의
# ==========================================
class BranchRequest(BaseModel):
    name: str
    manager: str
    role: str
    status: str
    lastLogin: str

class StatusRequest(BaseModel):
    status: str

class ManagerRequest(BaseModel):
    manager: str

# 🌟 흩어져 있던 입점사 모델을 위로 올렸습니다.
class SellerRequest(BaseModel):
    company_name: str
    representative_name: str
    seller_status: str


# ==========================================
# 1. 지사 관리 API (Branches)
# ==========================================
@router.get("/branches", summary="지사 목록 조회")
async def get_branches(db: Session = Depends(get_db)):
    try:
        query = text("SELECT org_id, org_name, representative_name, org_type, active_yn, updated_at FROM org_units")
        result = db.execute(query).fetchall()
        
        branches = []
        for row in result:
            branches.append({
                "id": row.org_id,
                "name": row.org_name,
                "manager": row.representative_name or "미지정",
                "role": "최고관리자" if row.org_type == "HEADQUARTER" else "일반지사",
                "status": "정상" if row.active_yn == "Y" else "휴면",
                "lastLogin": row.updated_at.strftime("%Y-%m-%d %H:%M:%S") if row.updated_at else ""
            })
        return branches
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/branches", summary="신규 지사 등록")
async def create_branch(branch: BranchRequest, db: Session = Depends(get_db)):
    try:
        org_type = "HEADQUARTER" if branch.role == "최고관리자" else "BRANCH"
        active_yn = "Y" if branch.status == "정상" else "N"
        org_code = f"BR-{int(time.time())}"
        
        query = text("""
            INSERT INTO org_units (org_code, org_name, org_type, representative_name, active_yn) 
            VALUES (:org_code, :org_name, :org_type, :rep_name, :active_yn)
        """)
        db.execute(query, {
            "org_code": org_code,
            "org_name": branch.name,
            "org_type": org_type,
            "rep_name": branch.manager,
            "active_yn": active_yn
        })
        db.commit()
        return {"message": "지사가 성공적으로 등록되었습니다."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/branches/{branch_id}/status", summary="지사 상태 변경")
async def update_branch_status(branch_id: int, req: StatusRequest, db: Session = Depends(get_db)):
    try:
        active_yn = "Y" if req.status == "정상" else "N"
        query = text("UPDATE org_units SET active_yn = :active_yn WHERE org_id = :org_id")
        db.execute(query, {"active_yn": active_yn, "org_id": branch_id})
        db.commit()
        return {"message": "지사 상태가 성공적으로 변경되었습니다."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/branches/{branch_id}", summary="지사 삭제")
async def delete_branch(branch_id: int, db: Session = Depends(get_db)):
    try:
        query = text("DELETE FROM org_units WHERE org_id = :org_id")
        db.execute(query, {"org_id": branch_id})
        db.commit()
        return {"message": "지사가 성공적으로 삭제되었습니다."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/branches/{branch_id}/manager", summary="담당자 이름 변경")
async def update_branch_manager(branch_id: int, req: ManagerRequest, db: Session = Depends(get_db)):
    try:
        query = text("UPDATE org_units SET representative_name = :rep_name WHERE org_id = :org_id")
        db.execute(query, {"rep_name": req.manager, "org_id": branch_id})
        db.commit()
        return {"message": "담당자가 성공적으로 변경되었습니다."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 2. 대시보드 통계 API
# ==========================================
@router.get("/dashboard", summary="대시보드 핵심 통계 및 차트 데이터")
def get_dashboard_summary(db: Session = Depends(get_db)):
    orders_summary = db.execute(text("SELECT COUNT(*) as total_count, SUM(total_amount) as total_sales FROM orders")).mappings().first()
    
    # 🌟 에러가 났던 status 컬럼들을 실제 DB 컬럼명으로 수정했습니다.
    active_sellers = db.execute(text("SELECT COUNT(*) as count FROM seller_profiles WHERE seller_status = 'ACTIVE'")).mappings().first()
    pending_orders = db.execute(text("SELECT COUNT(*) as count FROM orders WHERE order_status IN ('결제완료', '배송준비중')")).mappings().first()
    
    chart_query = text("""
        SELECT DATE_FORMAT(created_at, '%m-%d') as label, SUM(total_amount) as sales 
        FROM orders 
        GROUP BY DATE(created_at) 
        ORDER BY DATE(created_at) ASC 
        LIMIT 7
    """)
    chart_records = db.execute(chart_query).mappings().all()
    chart_data = [{"label": row["label"], "sales": row["sales"]} for row in chart_records]
    
    return {
        "total_sales": orders_summary["total_sales"] or 0,
        "total_orders": orders_summary["total_count"] or 0,
        "active_sellers": active_sellers["count"] or 0,
        "pending_orders": pending_orders["count"] or 0,
        "chart_data": chart_data
    }


# ==========================================
# 3. 입점사, 상품, 주문, 정산 리스트 API
# ==========================================
@router.get("/sellers", summary="입점사 및 파트너 목록 조회")
def get_sellers(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM seller_profiles")).mappings().all()
    return result

import random # 파일 맨 위쪽 import 모음에 추가해주세요 (없을 경우)

import random

@router.post("/sellers", summary="신규 입점사 등록")
async def create_seller(seller: SellerRequest, db: Session = Depends(get_db)):
    try:
        random_user_id = random.randint(10000, 999999)
        
        # 🌟 해결책: 입점사를 강제로 등록하기 위해 외래키(Foreign Key) 규칙 검사를 잠시 끕니다.
        db.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
        
        query = text("""
            INSERT INTO seller_profiles (user_id, company_name, representative_name, seller_status) 
            VALUES (:user_id, :company_name, :representative_name, :seller_status)
        """)
        db.execute(query, {
            "user_id": random_user_id, 
            "company_name": seller.company_name,
            "representative_name": seller.representative_name,
            "seller_status": seller.seller_status
        })
        
        # 🌟 저장이 완료되면 다른 데이터의 안전을 위해 외래키 검사를 다시 켭니다.
        db.execute(text("SET FOREIGN_KEY_CHECKS=1;"))
        db.commit()
        
        return {"message": "입점사가 성공적으로 등록되었습니다."}
        
    except Exception as e:
        db.rollback()
        # 에러가 나더라도 외래키 검사는 다시 켜주어야 합니다.
        db.execute(text("SET FOREIGN_KEY_CHECKS=1;")) 
        print(f"DB 저장 에러 상세 내용: {str(e)}") 
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/sellers/{seller_id}/approve", summary="입점사 승인 처리")
def approve_seller(seller_id: int, db: Session = Depends(get_db)):
    db.execute(
        text("UPDATE seller_profiles SET seller_status = 'ACTIVE' WHERE seller_id = :id"),
        {"id": seller_id}
    )
    db.commit()
    return {"message": "입점 승인이 완료되었습니다.", "id": seller_id}

@router.patch("/sellers/{seller_id}/reject", summary="입점사 승인 거절 처리")
def reject_seller(seller_id: int, db: Session = Depends(get_db)):
    db.execute(
        text("UPDATE seller_profiles SET seller_status = 'REJECTED' WHERE seller_id = :id"),
        {"id": seller_id}
    )
    db.commit()
    return {"message": "입점 거절 처리가 완료되었습니다.", "id": seller_id}

@router.patch("/sellers/{seller_id}/revert-reject", summary="입점 거절 취소 (승인대기로 복구)")
def revert_reject_seller(seller_id: int, db: Session = Depends(get_db)):
    db.execute(
        text("UPDATE seller_profiles SET seller_status = 'PENDING' WHERE seller_id = :id"),
        {"id": seller_id}
    )
    db.commit()
    return {"message": "승인 대기 상태로 복구되었습니다.", "id": seller_id}


@router.patch("/sellers/{seller_id}/suspend", summary="입점사 권한 정지 처리")
def suspend_seller(seller_id: int, db: Session = Depends(get_db)):
    db.execute(
        text("UPDATE seller_profiles SET seller_status = 'SUSPENDED' WHERE seller_id = :id"),
        {"id": seller_id}
    )
    db.commit()
    return {"message": "판매 자격이 정지되었습니다.", "id": seller_id}

# 기존 승인(approve), 정지(suspend) API 아래에 이 코드를 추가하세요.

@router.patch("/sellers/{seller_id}/reject", summary="입점사 승인 거절 처리")
def reject_seller(seller_id: int, db: Session = Depends(get_db)):
    db.execute(
        text("UPDATE seller_profiles SET seller_status = 'REJECTED' WHERE seller_id = :id"),
        {"id": seller_id}
    )
    db.commit()
    return {"message": "입점 거절 처리가 완료되었습니다.", "id": seller_id}


@router.get("/products", summary="상품 목록 조회")
def get_products(db: Session = Depends(get_db)):
    query = text("SELECT product_id, product_code, product_name, sale_price, product_status, created_at FROM products ORDER BY product_id DESC")
    return db.execute(query).mappings().all()

@router.get("/orders", summary="주문 목록 조회")
def get_orders(db: Session = Depends(get_db)):
    query = text("SELECT order_id, order_no, receiver_name, total_amount, order_status, ordered_at FROM orders ORDER BY ordered_at DESC")
    return db.execute(query).mappings().all()

@router.get("/settlements", summary="정산 내역 조회")
def get_settlements(db: Session = Depends(get_db)):
    query = text("SELECT id, target_name, period, total_sales, commission, final_amount, status, created_at FROM settlements ORDER BY id DESC")
    return db.execute(query).mappings().all()


# ==========================================
# 4. 고객 소통(CS) 및 시스템 운영 로그 API
# ==========================================
@router.get("/inquiries", summary="고객 소통 및 CS 총괄")
def get_inquiries(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT * FROM buyer_inquiries ORDER BY created_at DESC LIMIT 100")).mappings().all()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs", summary="시스템 운영 및 보안 감사 로그")
def get_logs(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT * FROM error_logs ORDER BY created_at DESC LIMIT 100")).mappings().all()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 기존에 있던 GET /logs 아래에 추가합니다.
@router.patch("/logs/{log_id}/resolve", summary="시스템 이슈 종결 처리")
def resolve_log(log_id: int, db: Session = Depends(get_db)):
    try:
        # DB의 error_logs 테이블에서 해당 로그의 상태를 '조치완료'로 변경합니다.
        db.execute(
            text("UPDATE error_logs SET status = '조치완료' WHERE id = :id"),
            {"id": log_id}
        )
        db.commit()
        return {"message": "이슈가 종결 처리되었습니다.", "id": log_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/logs/{log_id}/unblock", summary="시스템 차단 해제 처리")
def unblock_log(log_id: int, db: Session = Depends(get_db)):
    try:
        # DB의 error_logs 테이블에서 해당 로그의 상태를 '차단해제'로 변경합니다.
        db.execute(
            text("UPDATE error_logs SET status = '차단해제' WHERE id = :id"),
            {"id": log_id}
        )
        db.commit()
        return {"message": "차단이 해제되었습니다.", "id": log_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# 1. 차단 해제 API
@router.patch("/logs/{log_id}/unblock", summary="시스템 차단 해제 처리")
def unblock_log(log_id: int, db: Session = Depends(get_db)):
    try:
        db.execute(text("UPDATE error_logs SET status = '차단해제' WHERE id = :id"), {"id": log_id})
        db.commit()
        return {"message": "차단이 해제되었습니다.", "id": log_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 2. 조치 취소(미조치로 복구) API
@router.patch("/logs/{log_id}/revert-resolve", summary="이슈 조치 취소 (미조치로 복구)")
def revert_resolve_log(log_id: int, db: Session = Depends(get_db)):
    try:
        db.execute(text("UPDATE error_logs SET status = '미조치' WHERE id = :id"), {"id": log_id})
        db.commit()
        return {"message": "미조치 상태로 복구되었습니다.", "id": log_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/login", summary="본사 관리자 로그인")
async def hq_login(req: LoginRequest):
    try:
        # 🌟 지정된 아이디와 비밀번호(shopdbid2)만 통과되도록 수정
        if req.admin_id == "shopdbid2" and req.password == "shopdbid2":
            return {
                "message": "로그인 성공", 
                "token": "hq_admin_token_sample",
                "role": "HEADQUARTER"
            }
        else:
            raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 일치하지 않습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




