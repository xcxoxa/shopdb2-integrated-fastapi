from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import member2 as models
from app.schemas import member2 as schemas

router = APIRouter(prefix="/api/inventories", tags=["조원 2 지점별 재고"])

@router.get("", response_model=List[schemas.InventoryResponse], summary="전체 지점별 재고 조인 조회")
def get_inventories(db: Session = Depends(get_db)):
    query = db.query(
        models.Inventory.inventory_id,
        models.Inventory.org_id,
        models.Inventory.variant_id,
        models.ProductVariant.sku_code,
        models.Inventory.stock_quantity,
        models.Inventory.reserved_quantity,
        models.Inventory.safety_stock,
        models.Inventory.updated_at
    ).join(
        models.ProductVariant, models.Inventory.variant_id == models.ProductVariant.variant_id
    ).all()
    
    return [dict(row._mapping) for row in query]