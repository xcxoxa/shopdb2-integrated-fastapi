from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import member2 as models
from app.schemas import member2 as schemas

router = APIRouter(prefix="/api/products", tags=["조원 2 상품"])

@router.get("", response_model=List[schemas.ProductListResponse], summary="상품 목록 썸네일 조인 조회")
def get_products(db: Session = Depends(get_db)):
    query = db.query(
        models.Product.product_id,
        models.Product.product_code,
        models.Product.product_name,
        models.Category.category_name,
        models.Product.regular_price,
        models.Product.sale_price,
        models.FileAsset.public_url.label("main_image_url")
    ).join(
        models.Category, models.Product.category_id == models.Category.category_id
    ).outerjoin(
        models.ProductImage, (models.Product.product_id == models.ProductImage.product_id) & (models.ProductImage.image_type == 'MAIN')
    ).outerjoin(
        models.FileAsset, models.ProductImage.file_id == models.FileAsset.file_id
    ).all()
    
    return [dict(row._mapping) for row in query]

@router.get("/{product_id}", response_model=schemas.ProductDetailResponse, summary="특정 상품 상세 통합 조회 (이미지, 첨부파일, 옵션, 재고 포함)")
def get_product(product_id: int, db: Session = Depends(get_db)):
    # 1. 상품 마스터 조회
    product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    # 2. 상품 이미지 목록 조회 (file_assets 조인)
    images_query = db.query(
        models.ProductImage.product_image_id,
        models.ProductImage.image_type,
        models.ProductImage.display_order,
        models.FileAsset.public_url,
        models.FileAsset.thumbnail_url
    ).join(
        models.FileAsset, models.ProductImage.file_id == models.FileAsset.file_id
    ).filter(models.ProductImage.product_id == product_id).all()
    
    images = [dict(row._mapping) for row in images_query]

    # 3. 상품 첨부파일 목록 조회 (product_files 및 file_assets 조인)
    files_query = db.query(
        models.ProductFile.product_file_id,
        models.ProductFile.file_category,
        models.ProductFile.file_description,
        models.FileAsset.public_url,
        models.FileAsset.original_file_name
    ).join(
        models.FileAsset, models.ProductFile.file_id == models.FileAsset.file_id
    ).filter(models.ProductFile.product_id == product_id).all()

    files = [dict(row._mapping) for row in files_query]

    # 4. 상품 옵션 (SKU) 목록 조회
    variants = db.query(models.ProductVariant).filter(models.ProductVariant.product_id == product_id).all()

    # 5. 지점별 재고 목록 조회 (옵션과 조인)
    variant_ids = [v.variant_id for v in variants]
    inventories = []
    if variant_ids:
        inv_query = db.query(
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
        ).filter(models.Inventory.variant_id.in_(variant_ids)).all()
        
        inventories = [dict(row._mapping) for row in inv_query]

    # 6. 결과 데이터 조립 반환
    result = dict(product.__dict__)
    result["images"] = images
    result["files"] = files
    result["variants"] = variants
    result["inventories"] = inventories

    return result