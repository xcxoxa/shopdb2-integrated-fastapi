from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db


router = APIRouter(prefix="/api/branch", tags=["지사 관리자"])


class BranchProductRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(ge=0)
    stock: int = Field(ge=0)


class BranchOrderStatusRequest(BaseModel):
    order_status: str = Field(min_length=1, max_length=30)


def branch_id(x_org_id: int = Header(..., alias="X-Org-Id", gt=0)) -> int:
    return x_org_id


def require_branch(db: Session, org_id: int) -> dict:
    row = db.execute(
        text("SELECT * FROM org_units WHERE org_id = :org_id"),
        {"org_id": org_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="지사 정보를 찾을 수 없습니다.")
    return dict(row)


def require_branch_product(db: Session, org_id: int, product_id: int) -> None:
    found = db.execute(
        text(
            """
            SELECT 1
            FROM inventories i
            JOIN product_variants pv ON pv.variant_id = i.variant_id
            WHERE i.org_id = :org_id AND pv.product_id = :product_id
            LIMIT 1
            """
        ),
        {"org_id": org_id, "product_id": product_id},
    ).first()
    if found is None:
        raise HTTPException(status_code=404, detail="이 지사에서 관리하는 상품이 아닙니다.")


@router.get("/me")
def get_branch(org_id: int = Depends(branch_id), db: Session = Depends(get_db)) -> dict:
    return require_branch(db, org_id)


@router.get("/dashboard")
def get_dashboard(org_id: int = Depends(branch_id), db: Session = Depends(get_db)) -> dict:
    branch = require_branch(db, org_id)
    metrics = db.execute(
        text(
            """
            SELECT
              (SELECT COUNT(DISTINCT pv.product_id)
                 FROM inventories i
                 JOIN product_variants pv ON pv.variant_id = i.variant_id
                 JOIN products p ON p.product_id = pv.product_id
                 JOIN categories c ON c.category_id = p.category_id
                WHERE i.org_id = :org_id
                  AND c.category_name IN ('상의', '하의', '아우터', '신발')) AS product_count,
              (SELECT COALESCE(SUM(i.stock_quantity), 0)
                 FROM inventories i
                 JOIN product_variants pv ON pv.variant_id = i.variant_id
                 JOIN products p ON p.product_id = pv.product_id
                 JOIN categories c ON c.category_id = p.category_id
                WHERE i.org_id = :org_id
                  AND c.category_name IN ('상의', '하의', '아우터', '신발')) AS total_stock,
              (SELECT COUNT(*) FROM orders o
                WHERE o.org_id = :org_id AND DATE(o.ordered_at) = CURRENT_DATE
                  AND EXISTS (
                    SELECT 1 FROM order_items oi
                    JOIN products p ON p.product_id = oi.product_id
                    JOIN categories c ON c.category_id = p.category_id
                    WHERE oi.order_id = o.order_id
                      AND c.category_name IN ('상의', '하의', '아우터', '신발')
                  )) AS today_orders,
              (SELECT COALESCE(SUM(o.total_amount), 0) FROM orders o
                WHERE o.org_id = :org_id AND o.order_status NOT IN ('CANCELLED', 'CANCELED')
                  AND EXISTS (
                    SELECT 1 FROM order_items oi
                    JOIN products p ON p.product_id = oi.product_id
                    JOIN categories c ON c.category_id = p.category_id
                    WHERE oi.order_id = o.order_id
                      AND c.category_name IN ('상의', '하의', '아우터', '신발')
                  )) AS total_sales
            """
        ),
        {"org_id": org_id},
    ).mappings().one()
    return {"branch": branch, **dict(metrics)}


@router.get("/products")
def get_products(org_id: int = Depends(branch_id), db: Session = Depends(get_db)) -> list[dict]:
    require_branch(db, org_id)
    rows = db.execute(
        text(
            """
            SELECT p.product_id, p.product_code, p.product_name, c.category_name,
                   p.regular_price, p.sale_price, p.product_status,
                   COALESCE(SUM(i.stock_quantity), 0) AS stock_quantity,
                   COALESCE(SUM(i.reserved_quantity), 0) AS reserved_quantity,
                   COALESCE(SUM(i.safety_stock), 0) AS safety_stock
            FROM inventories i
            JOIN product_variants pv ON pv.variant_id = i.variant_id
            JOIN products p ON p.product_id = pv.product_id
            JOIN categories c ON c.category_id = p.category_id
            WHERE i.org_id = :org_id AND p.product_status <> 'DELETED'
              AND c.category_name IN ('상의', '하의', '아우터', '신발')
            GROUP BY p.product_id, p.product_code, p.product_name, c.category_name,
                     p.regular_price, p.sale_price, p.product_status
            ORDER BY p.product_id DESC
            """
        ),
        {"org_id": org_id},
    ).mappings().all()
    return [dict(row) for row in rows]


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(request: BranchProductRequest, org_id: int = Depends(branch_id), db: Session = Depends(get_db)) -> dict:
    require_branch(db, org_id)
    try:
        category_id = db.execute(
            text("SELECT category_id FROM categories WHERE category_name = :name LIMIT 1"),
            {"name": request.category.strip()},
        ).scalar()
        if category_id is None:
            result = db.execute(
                text("INSERT INTO categories (category_name, category_level, display_order, active_yn) VALUES (:name, 1, 0, 'Y')"),
                {"name": request.category.strip()},
            )
            category_id = result.lastrowid
        seller_user_id = db.execute(text("SELECT user_id FROM seller_profiles ORDER BY seller_id LIMIT 1")).scalar() or 1
        code = f"B{org_id}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        result = db.execute(
            text(
                """
                INSERT INTO products (seller_user_id, category_id, product_code, product_name,
                                      regular_price, sale_price, product_status, created_at, updated_at)
                VALUES (:seller_user_id, :category_id, :code, :name, :price, :price,
                        :product_status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            {"seller_user_id": seller_user_id, "category_id": category_id, "code": code,
             "name": request.name.strip(), "price": request.price,
             "product_status": "SALE" if request.stock > 0 else "SOLD_OUT"},
        )
        product_id = result.lastrowid
        variant = db.execute(
            text("INSERT INTO product_variants (product_id, sku_code, option_name1, option_value1, additional_price, active_yn) VALUES (:product_id, :sku, '기본 옵션', '기본', 0, 'Y')"),
            {"product_id": product_id, "sku": f"SKU-{code}"},
        )
        db.execute(
            text("INSERT INTO inventories (org_id, variant_id, stock_quantity, reserved_quantity, safety_stock, updated_at) VALUES (:org_id, :variant_id, :stock, 0, 0, CURRENT_TIMESTAMP)"),
            {"org_id": org_id, "variant_id": variant.lastrowid, "stock": request.stock},
        )
        db.commit()
        return {"message": "지사 상품을 등록했습니다.", "product_id": product_id}
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"상품 등록 실패: {error}") from error


@router.put("/products/{product_id}")
def update_product(product_id: int, request: BranchProductRequest, org_id: int = Depends(branch_id), db: Session = Depends(get_db)) -> dict:
    require_branch(db, org_id)
    require_branch_product(db, org_id, product_id)
    try:
        category_id = db.execute(text("SELECT category_id FROM categories WHERE category_name = :name LIMIT 1"), {"name": request.category.strip()}).scalar()
        if category_id is None:
            result = db.execute(text("INSERT INTO categories (category_name, category_level, display_order, active_yn) VALUES (:name, 1, 0, 'Y')"), {"name": request.category.strip()})
            category_id = result.lastrowid
        db.execute(
            text("UPDATE products SET category_id=:category_id, product_name=:name, regular_price=:price, sale_price=:price, product_status=:status, updated_at=CURRENT_TIMESTAMP WHERE product_id=:product_id"),
            {"category_id": category_id, "name": request.name.strip(), "price": request.price,
             "status": "SALE" if request.stock > 0 else "SOLD_OUT", "product_id": product_id},
        )
        inventories = db.execute(
            text("SELECT i.inventory_id FROM inventories i JOIN product_variants pv ON pv.variant_id=i.variant_id WHERE i.org_id=:org_id AND pv.product_id=:product_id ORDER BY i.inventory_id"),
            {"org_id": org_id, "product_id": product_id},
        ).scalars().all()
        db.execute(
            text("UPDATE inventories i JOIN product_variants pv ON pv.variant_id=i.variant_id SET i.stock_quantity=0, i.updated_at=CURRENT_TIMESTAMP WHERE i.org_id=:org_id AND pv.product_id=:product_id"),
            {"org_id": org_id, "product_id": product_id},
        )
        db.execute(text("UPDATE inventories SET stock_quantity=:stock, updated_at=CURRENT_TIMESTAMP WHERE inventory_id=:inventory_id"), {"stock": request.stock, "inventory_id": inventories[0]})
        db.commit()
        return {"message": "지사 상품과 재고를 수정했습니다.", "product_id": product_id}
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"상품 수정 실패: {error}") from error


@router.delete("/products/{product_id}")
def stop_product(product_id: int, org_id: int = Depends(branch_id), db: Session = Depends(get_db)) -> dict:
    require_branch(db, org_id)
    require_branch_product(db, org_id, product_id)
    db.execute(
        text("UPDATE inventories i JOIN product_variants pv ON pv.variant_id=i.variant_id SET i.stock_quantity=0, i.reserved_quantity=0, i.updated_at=CURRENT_TIMESTAMP WHERE i.org_id=:org_id AND pv.product_id=:product_id"),
        {"org_id": org_id, "product_id": product_id},
    )
    db.commit()
    return {"message": "이 지사의 상품 판매를 중지했습니다.", "product_id": product_id}


@router.get("/orders")
def get_orders(org_id: int = Depends(branch_id), db: Session = Depends(get_db)) -> list[dict]:
    require_branch(db, org_id)
    rows = db.execute(
        text(
            """
            SELECT o.order_id, o.order_no, o.buyer_user_id, u.user_name AS buyer_name,
                   o.order_status, o.total_amount, o.ordered_at
            FROM orders o JOIN users u ON u.user_id = o.buyer_user_id
            WHERE o.org_id = :org_id
              AND EXISTS (
                SELECT 1
                FROM order_items oi
                JOIN products p ON p.product_id = oi.product_id
                JOIN categories c ON c.category_id = p.category_id
                WHERE oi.order_id = o.order_id
                  AND c.category_name IN ('상의', '하의', '아우터', '신발')
              )
            ORDER BY o.ordered_at DESC, o.order_id DESC
            """
        ),
        {"org_id": org_id},
    ).mappings().all()
    return [dict(row) for row in rows]


@router.patch("/orders/{order_id}/status")
def update_order_status(order_id: int, request: BranchOrderStatusRequest, org_id: int = Depends(branch_id), db: Session = Depends(get_db)) -> dict:
    require_branch(db, org_id)
    requested = request.order_status.strip().upper()
    allowed = {"ORDERED", "PAYMENT_PENDING", "PAID", "PREPARING", "SHIPPING", "SHIPPED", "DELIVERING", "DELIVERED", "COMPLETED", "CANCELLED", "CANCELED", "REFUNDED"}
    if requested not in allowed:
        raise HTTPException(status_code=400, detail="허용되지 않는 주문 상태입니다.")
    result = db.execute(
        text("UPDATE orders SET order_status=:status, updated_at=CURRENT_TIMESTAMP WHERE order_id=:order_id AND org_id=:org_id"),
        {"status": requested, "order_id": order_id, "org_id": org_id},
    )
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=404, detail="이 지사의 주문을 찾을 수 없습니다.")
    db.commit()
    return {"message": "주문 상태를 변경했습니다.", "order_id": order_id, "order_status": requested}


@router.get("/customers")
def get_customers(org_id: int = Depends(branch_id), db: Session = Depends(get_db)) -> list[dict]:
    require_branch(db, org_id)
    rows = db.execute(
        text(
            """
            SELECT DISTINCT u.user_id, u.login_id, u.user_name, u.email,
                   u.phone, u.user_status, u.created_at
            FROM users u
            JOIN orders o ON o.buyer_user_id = u.user_id
            WHERE o.org_id = :org_id
              AND EXISTS (
                SELECT 1
                FROM order_items oi
                JOIN products p ON p.product_id = oi.product_id
                JOIN categories c ON c.category_id = p.category_id
                WHERE oi.order_id = o.order_id
                  AND c.category_name IN ('상의', '하의', '아우터', '신발')
              )
            ORDER BY u.user_id DESC
            """
        ),
        {"org_id": org_id},
    ).mappings().all()
    return [dict(row) for row in rows]
