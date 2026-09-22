from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
import time

from app.database import get_db


router = APIRouter(prefix="/api/hq", tags=["본사 관리(HQ)"])


class BranchRequest(BaseModel):
    name: str
    manager: str = ""
    role: str = "일반지사"
    status: str = "정상"
    lastLogin: str = ""


class StatusRequest(BaseModel):
    status: str


class ManagerRequest(BaseModel):
    manager: str


class SellerRequest(BaseModel):
    company_name: str
    representative_name: str
    seller_status: str = "PENDING"


def _updated(result, message: str):
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="대상을 찾을 수 없습니다.")
    return {"message": message}


@router.get("/branches")
def get_branches(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT org_id, org_name, representative_name, org_type, active_yn, updated_at
        FROM org_units ORDER BY org_id
    """)).mappings().all()
    return [{
        "id": row["org_id"], "name": row["org_name"],
        "manager": row["representative_name"] or "미지정",
        "role": "최고관리자" if row["org_type"] == "HEADQUARTER" else "일반지사",
        "status": "정상" if row["active_yn"] == "Y" else "휴면",
        "lastLogin": row["updated_at"].strftime("%Y-%m-%d %H:%M:%S") if row["updated_at"] else "",
    } for row in rows]


@router.post("/branches", status_code=201)
def create_branch(branch: BranchRequest, db: Session = Depends(get_db)):
    try:
        db.execute(text("""
            INSERT INTO org_units
                (org_code, org_name, org_type, representative_name, active_yn)
            VALUES (:code, :name, :type, :manager, :active)
        """), {
            "code": f"BR-{int(time.time())}", "name": branch.name,
            "type": "HEADQUARTER" if branch.role == "최고관리자" else "BRANCH",
            "manager": branch.manager, "active": "Y" if branch.status == "정상" else "N",
        })
        db.commit()
        return {"message": "지사가 성공적으로 등록되었습니다."}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/branches/{branch_id}/status")
def update_branch_status(branch_id: int, req: StatusRequest, db: Session = Depends(get_db)):
    result = db.execute(text("UPDATE org_units SET active_yn=:active WHERE org_id=:id"),
                        {"active": "Y" if req.status == "정상" else "N", "id": branch_id})
    db.commit()
    return _updated(result, "지사 상태가 변경되었습니다.")


@router.patch("/branches/{branch_id}/manager")
def update_branch_manager(branch_id: int, req: ManagerRequest, db: Session = Depends(get_db)):
    result = db.execute(text("UPDATE org_units SET representative_name=:manager WHERE org_id=:id"),
                        {"manager": req.manager, "id": branch_id})
    db.commit()
    return _updated(result, "담당자가 변경되었습니다.")


@router.delete("/branches/{branch_id}")
def delete_branch(branch_id: int, db: Session = Depends(get_db)):
    try:
        result = db.execute(text("DELETE FROM org_units WHERE org_id=:id"), {"id": branch_id})
        db.commit()
        return _updated(result, "지사가 삭제되었습니다.")
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="연결된 데이터가 있어 삭제할 수 없습니다.") from exc


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    orders = db.execute(text("SELECT COUNT(*) count, COALESCE(SUM(total_amount),0) sales FROM orders")).mappings().one()
    sellers = db.execute(text("SELECT COUNT(*) FROM seller_profiles WHERE seller_status='ACTIVE'")).scalar() or 0
    pending = db.execute(text("SELECT COUNT(*) FROM orders WHERE order_status IN ('PAID','PREPARING')")).scalar() or 0
    chart = db.execute(text("""
        SELECT DATE_FORMAT(ordered_at,'%m-%d') label, COALESCE(SUM(total_amount),0) sales
        FROM orders GROUP BY DATE(ordered_at) ORDER BY DATE(ordered_at) DESC LIMIT 7
    """)).mappings().all()
    return {"total_sales": orders["sales"], "total_orders": orders["count"],
            "active_sellers": sellers, "pending_orders": pending,
            "chart_data": [dict(row) for row in reversed(chart)]}


@router.get("/sellers")
def get_sellers(db: Session = Depends(get_db)):
    return [dict(row) for row in db.execute(text("SELECT * FROM seller_profiles ORDER BY seller_id DESC")).mappings().all()]


@router.post("/sellers", status_code=201)
def create_seller(req: SellerRequest, db: Session = Depends(get_db)):
    user_id = db.execute(text("""
        SELECT u.user_id FROM users u
        JOIN roles r ON r.role_id=u.role_id
        LEFT JOIN seller_profiles sp ON sp.user_id=u.user_id
        WHERE r.role_code='SELLER' AND sp.seller_id IS NULL
        ORDER BY u.user_id LIMIT 1
    """)).scalar()
    if user_id is None:
        raise HTTPException(status_code=409, detail="입점사 프로필에 연결할 미등록 SELLER 사용자가 없습니다.")
    db.execute(text("""
        INSERT INTO seller_profiles(user_id,company_name,representative_name,seller_status)
        VALUES(:user_id,:company,:representative,:status)
    """), {"user_id": user_id, "company": req.company_name,
             "representative": req.representative_name, "status": req.seller_status})
    db.commit()
    return {"message": "입점사가 등록되었습니다."}


def _seller_status(seller_id: int, value: str, db: Session):
    result = db.execute(text("UPDATE seller_profiles SET seller_status=:status WHERE seller_id=:id"),
                        {"status": value, "id": seller_id})
    db.commit()
    return _updated(result, "입점사 상태가 변경되었습니다.")


@router.patch("/sellers/{seller_id}/approve")
def approve_seller(seller_id: int, db: Session = Depends(get_db)):
    return _seller_status(seller_id, "ACTIVE", db)


@router.patch("/sellers/{seller_id}/reject")
def reject_seller(seller_id: int, db: Session = Depends(get_db)):
    return _seller_status(seller_id, "REJECTED", db)


@router.patch("/sellers/{seller_id}/revert-reject")
def revert_seller(seller_id: int, db: Session = Depends(get_db)):
    return _seller_status(seller_id, "PENDING", db)


@router.patch("/sellers/{seller_id}/suspend")
def suspend_seller(seller_id: int, db: Session = Depends(get_db)):
    return _seller_status(seller_id, "SUSPENDED", db)


@router.get("/products")
def get_products(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT product_id,product_code,product_name,sale_price,product_status,created_at
        FROM products ORDER BY product_id DESC
    """)).mappings().all()
    return [dict(row) for row in rows]


@router.get("/orders")
def get_orders(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT order_id,order_no,receiver_name,total_amount,order_status,ordered_at
        FROM orders ORDER BY ordered_at DESC
    """)).mappings().all()
    return [dict(row) for row in rows]


@router.get("/settlements")
def get_settlements(db: Session = Depends(get_db)):
    try:
        rows = db.execute(text("""
            SELECT id,target_name,period,total_sales,commission,final_amount,status,created_at
            FROM settlements ORDER BY id DESC
        """)).mappings().all()
        return [dict(row) for row in rows]
    except Exception:
        db.rollback()
        return []


@router.get("/inquiries")
def get_inquiries(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT bi.inquiry_id id, bi.inquiry_no,
               bi.inquiry_type type, bi.inquiry_title title,
               u.login_id author,
               CASE bi.inquiry_status WHEN 'ANSWERED' THEN '답변완료'
                    WHEN 'PROCESSING' THEN '처리중' ELSE '미답변' END status,
               bi.answer_content reply, bi.created_at
        FROM buyer_inquiries bi JOIN users u ON u.user_id=bi.buyer_user_id
        ORDER BY bi.created_at DESC LIMIT 100
    """)).mappings().all()
    return [dict(row) for row in rows]


@router.get("/logs")
def get_logs(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM error_logs ORDER BY error_log_id DESC LIMIT 100")).mappings().all()
    return [{**dict(row), "id": row["error_log_id"]} for row in rows]


@router.get("/routes")
def route_health():
    return {"status": "ok", "prefix": "/api/hq"}
