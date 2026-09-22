from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import member2 as models
from app.schemas import member2 as schemas

router = APIRouter(prefix="/api/products", tags=["조원 2 상품"])


class ProductAdminRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(ge=0)
    stock: int = Field(ge=0)


def find_or_create_category(db: Session, name: str):
    name = name.strip()
    category = db.query(models.Category).filter(
        models.Category.category_name == name
    ).first()
    if category is None:
        category = models.Category(
            category_name=name,
            category_level=1,
            display_order=0,
            active_yn="Y",
        )
        db.add(category)
        db.flush()
    return category


def default_seller_user_id(db: Session) -> int:
    product = db.query(models.Product).order_by(
        models.Product.product_id
    ).first()
    if product is not None:
        return int(product.seller_user_id)
    seller = db.query(models.SellerProfile).order_by(
        models.SellerProfile.seller_id
    ).first()
    return int(seller.user_id) if seller is not None else 1


def default_org_id(db: Session) -> int:
    inventory = db.query(models.Inventory).order_by(
        models.Inventory.inventory_id
    ).first()
    return int(inventory.org_id) if inventory is not None else 1


def set_product_stock(db: Session, product, stock: int) -> None:
    variants = db.query(models.ProductVariant).filter(
        models.ProductVariant.product_id == product.product_id
    ).order_by(models.ProductVariant.variant_id).all()

    if not variants:
        variant = models.ProductVariant(
            product_id=product.product_id,
            sku_code=f"SKU-{product.product_code}",
            option_name1="기본 옵션",
            option_value1="기본",
            additional_price=0,
            active_yn="Y",
        )
        db.add(variant)
        db.flush()
        variants = [variant]

    variant_ids = [variant.variant_id for variant in variants]
    inventories = db.query(models.Inventory).filter(
        models.Inventory.variant_id.in_(variant_ids)
    ).order_by(models.Inventory.inventory_id).all()

    if inventories:
        inventories[0].stock_quantity = stock
        for inventory in inventories[1:]:
            inventory.stock_quantity = 0
    else:
        db.add(models.Inventory(
            org_id=default_org_id(db),
            variant_id=variants[0].variant_id,
            stock_quantity=stock,
            reserved_quantity=0,
            safety_stock=0,
        ))


def product_list_query(db: Session):
    stock_query = db.query(
        models.ProductVariant.product_id.label("product_id"),
        func.coalesce(
            func.sum(models.Inventory.stock_quantity), 0
        ).label("stock_quantity"),
    ).outerjoin(
        models.Inventory,
        models.ProductVariant.variant_id == models.Inventory.variant_id,
    ).group_by(
        models.ProductVariant.product_id
    ).subquery()

    return db.query(
        models.Product.product_id,
        models.Product.product_code,
        models.Product.product_name,
        models.Category.category_name,
        models.Product.regular_price,
        models.Product.sale_price,
        models.Product.product_status,
        models.FileAsset.public_url.label("main_image_url"),
        func.coalesce(
            stock_query.c.stock_quantity, 0
        ).label("stock_quantity"),
    ).join(
        models.Category,
        models.Product.category_id == models.Category.category_id,
    ).outerjoin(
        stock_query,
        models.Product.product_id == stock_query.c.product_id,
    ).outerjoin(
        models.ProductImage,
        (models.Product.product_id == models.ProductImage.product_id)
        & (models.ProductImage.image_type == "MAIN"),
    ).outerjoin(
        models.FileAsset,
        models.ProductImage.file_id == models.FileAsset.file_id,
    ).filter(
        models.Product.product_status != "DELETED"
    )


@router.get("", summary="상품 목록 및 재고 합계 조회")
def get_products(db: Session = Depends(get_db)):
    return [
        dict(row._mapping)
        for row in product_list_query(db).all()
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_product(
    request: ProductAdminRequest,
    db: Session = Depends(get_db),
):
    try:
        category = find_or_create_category(db, request.category)
        code = f"P{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        product = models.Product(
            seller_user_id=default_seller_user_id(db),
            category_id=category.category_id,
            product_code=code,
            product_name=request.name.strip(),
            regular_price=request.price,
            sale_price=request.price,
            product_status="SALE" if request.stock > 0 else "SOLD_OUT",
        )
        db.add(product)
        db.flush()
        set_product_stock(db, product, request.stock)
        db.commit()
        return {
            "message": "상품을 등록했습니다.",
            "product_id": product.product_id,
        }
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"상품 등록 실패: {error}",
        ) from error


@router.put("/{product_id}")
def update_product(
    product_id: int,
    request: ProductAdminRequest,
    db: Session = Depends(get_db),
):
    product = db.query(models.Product).filter(
        models.Product.product_id == product_id,
        models.Product.product_status != "DELETED",
    ).first()
    if product is None:
        raise HTTPException(404, "상품을 찾을 수 없습니다.")

    try:
        category = find_or_create_category(db, request.category)
        product.category_id = category.category_id
        product.product_name = request.name.strip()
        product.regular_price = request.price
        product.sale_price = request.price
        product.product_status = (
            "SALE" if request.stock > 0 else "SOLD_OUT"
        )
        set_product_stock(db, product, request.stock)
        db.commit()
        return {
            "message": "상품을 수정했습니다.",
            "product_id": product.product_id,
        }
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"상품 수정 실패: {error}",
        ) from error


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.query(models.Product).filter(
        models.Product.product_id == product_id,
        models.Product.product_status != "DELETED",
    ).first()
    if product is None:
        raise HTTPException(404, "상품을 찾을 수 없습니다.")

    try:
        product.product_status = "DELETED"
        set_product_stock(db, product, 0)
        db.commit()
        return {
            "message": "상품을 삭제했습니다.",
            "product_id": product.product_id,
        }
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"상품 삭제 실패: {error}",
        ) from error


@router.get(
    "/{product_id}",
    response_model=schemas.ProductDetailResponse,
    summary="특정 상품 상세 통합 조회",
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.query(models.Product).filter(
        models.Product.product_id == product_id,
        models.Product.product_status != "DELETED",
    ).first()
    if product is None:
        raise HTTPException(404, "상품을 찾을 수 없습니다.")

    images = db.query(
        models.ProductImage.product_image_id,
        models.ProductImage.image_type,
        models.ProductImage.display_order,
        models.FileAsset.public_url,
        models.FileAsset.thumbnail_url,
    ).join(
        models.FileAsset,
        models.ProductImage.file_id == models.FileAsset.file_id,
    ).filter(
        models.ProductImage.product_id == product_id
    ).all()

    files = db.query(
        models.ProductFile.product_file_id,
        models.ProductFile.file_category,
        models.ProductFile.file_description,
        models.FileAsset.public_url,
        models.FileAsset.original_file_name,
    ).join(
        models.FileAsset,
        models.ProductFile.file_id == models.FileAsset.file_id,
    ).filter(
        models.ProductFile.product_id == product_id
    ).all()

    variants = db.query(models.ProductVariant).filter(
        models.ProductVariant.product_id == product_id
    ).all()
    variant_ids = [variant.variant_id for variant in variants]
    inventories = []

    if variant_ids:
        inventories = db.query(
            models.Inventory.inventory_id,
            models.Inventory.org_id,
            models.Inventory.variant_id,
            models.ProductVariant.sku_code,
            models.Inventory.stock_quantity,
            models.Inventory.reserved_quantity,
            models.Inventory.safety_stock,
            models.Inventory.updated_at,
        ).join(
            models.ProductVariant,
            models.Inventory.variant_id == models.ProductVariant.variant_id,
        ).filter(
            models.Inventory.variant_id.in_(variant_ids)
        ).all()

    result = dict(product.__dict__)
    result.pop("_sa_instance_state", None)
    result["images"] = [dict(row._mapping) for row in images]
    result["files"] = [dict(row._mapping) for row in files]
    result["variants"] = variants
    result["inventories"] = [
        dict(row._mapping) for row in inventories
    ]
    return result
