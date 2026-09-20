from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# 1. 카테고리 스키마
class CategoryBase(BaseModel):
    parent_category_id: Optional[int] = None
    category_name: str
    category_level: int = 1
    display_order: int = 0
    active_yn: str = 'Y'

class CategoryResponse(CategoryBase):
    category_id: int

    class Config:
        from_attributes = True

# 2. 판매자 프로필 스키마
class SellerProfileBase(BaseModel):
    company_name: str
    business_number: Optional[str] = None
    representative_name: Optional[str] = None
    settlement_bank: Optional[str] = None
    settlement_account: Optional[str] = None

class SellerProfileResponse(SellerProfileBase):
    seller_id: int
    user_id: int
    seller_status: str
    created_at: datetime

    class Config:
        from_attributes = True

# 3. 상품 마스터 스키마
class ProductBase(BaseModel):
    seller_user_id: int
    category_id: int
    product_code: str
    product_name: str
    short_description: Optional[str] = None
    regular_price: Decimal
    sale_price: Decimal
    product_status: str = 'READY'

class ProductResponse(ProductBase):
    product_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 4. 파일 공통 관리 스키마
class FileAssetBase(BaseModel):
    file_type: str
    storage_type: str
    original_file_name: Optional[str] = None
    public_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

class FileAssetResponse(FileAssetBase):
    file_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# 5. 상품 이미지 응답 스키마
class ProductImageResponse(BaseModel):
    product_image_id: int
    image_type: str
    display_order: int
    public_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    class Config:
        from_attributes = True

# 6. 상품 첨부파일 응답 스키마
class ProductFileResponse(BaseModel):
    product_file_id: int
    file_category: Optional[str] = None
    file_description: Optional[str] = None
    public_url: Optional[str] = None
    original_file_name: Optional[str] = None

    class Config:
        from_attributes = True

# 7. 상품 옵션 (SKU) 스키마
class ProductVariantResponse(BaseModel):
    variant_id: int
    sku_code: str
    option_name1: Optional[str] = None
    option_value1: Optional[str] = None
    option_name2: Optional[str] = None
    option_value2: Optional[str] = None
    additional_price: Decimal
    active_yn: str

    class Config:
        from_attributes = True

# 8. 지점별 재고 스키마
class InventoryResponse(BaseModel):
    inventory_id: int
    org_id: int
    variant_id: int
    sku_code: str
    stock_quantity: int
    reserved_quantity: int
    safety_stock: int
    updated_at: datetime

    class Config:
        from_attributes = True

# 9. 상품 목록 조인(JOIN) 결과 스키마
class ProductListResponse(BaseModel):
    product_id: int
    product_code: str
    product_name: str
    category_name: str
    regular_price: Decimal
    sale_price: Decimal
    main_image_url: Optional[str] = None

    class Config:
        from_attributes = True

# 10. 상품 상세 통합 조회 스키마 (이미지, 첨부파일, 옵션, 재고 포함)
class ProductDetailResponse(BaseModel):
    product_id: int
    seller_user_id: int
    category_id: int
    product_code: str
    product_name: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    regular_price: Decimal
    sale_price: Decimal
    product_status: str
    images: List[ProductImageResponse] = []
    files: List[ProductFileResponse] = []
    variants: List[ProductVariantResponse] = []
    inventories: List[InventoryResponse] = []

    class Config:
        from_attributes = True

        # ==========================================
# [확장 프로젝트] 조원 2 담당: 버전·배포·백업·롤백 스키마
# ==========================================

# 1. 앱 버전 관리 스키마
class ApplicationVersionResponse(BaseModel):
    version_id: int
    version_name: str
    git_commit_hash: str
    release_notes: Optional[str] = None
    version_status: str
    created_by_user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# 2. 배포 이력 스키마
class DeploymentHistoryResponse(BaseModel):
    deployment_id: int
    version_id: int
    environment_type: str
    deployment_status: str
    deployed_by_user_id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deployment_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# 3. DB 백업 이력 스키마
class DatabaseBackupHistoryResponse(BaseModel):
    backup_id: int
    version_id: Optional[int] = None
    backup_name: str
    backup_type: str
    storage_path: str
    checksum_sha256: Optional[str] = None
    file_size_bytes: Optional[int] = None
    backup_status: str
    created_by_user_id: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 4. 롤백 이력 스키마
class RollbackHistoryResponse(BaseModel):
    rollback_id: int
    from_version_id: int
    to_version_id: int
    deployment_id: Optional[int] = None
    backup_id: Optional[int] = None
    rollback_reason: str
    rollback_status: str
    requested_by_user_id: int
    approved_by_user_id: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# 5. 피처 플래그(기능 제어) 스키마
class FeatureFlagResponse(BaseModel):
    feature_flag_id: int
    flag_code: str
    flag_name: str
    description: Optional[str] = None
    enabled_yn: str
    target_role_code: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    updated_by_user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True