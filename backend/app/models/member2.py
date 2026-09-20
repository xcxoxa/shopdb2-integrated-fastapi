from sqlalchemy import Column, BigInteger, String, Integer, DECIMAL, ForeignKey, Enum, Text, DateTime, CHAR
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# 1. 카테고리
class Category(Base):
    __tablename__ = 'categories'
    category_id = Column(BigInteger, primary_key=True, autoincrement=True)
    parent_category_id = Column(BigInteger, ForeignKey('categories.category_id'))
    category_name = Column(String(100), nullable=False)
    category_level = Column(Integer, default=1)
    display_order = Column(Integer, default=0)
    active_yn = Column(CHAR(1), default='Y')

# 2. 판매자 프로필
class SellerProfile(Base):
    __tablename__ = 'seller_profiles'
    seller_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False) # users 테이블 연결
    company_name = Column(String(200), nullable=False)
    business_number = Column(String(30))
    representative_name = Column(String(100))
    settlement_bank = Column(String(100))
    settlement_account = Column(String(100))
    seller_status = Column(String(30), default='ACTIVE')
    created_at = Column(DateTime, default=datetime.utcnow)

# 3. 상품 마스터
class Product(Base):
    __tablename__ = 'products'
    product_id = Column(BigInteger, primary_key=True, autoincrement=True)
    seller_user_id = Column(BigInteger, nullable=False) 
    category_id = Column(BigInteger, ForeignKey('categories.category_id'), nullable=False)
    product_code = Column(String(50), unique=True, nullable=False)
    product_name = Column(String(200), nullable=False)
    short_description = Column(String(1000))
    description = Column(Text)
    regular_price = Column(DECIMAL(15,2), nullable=False)
    sale_price = Column(DECIMAL(15,2), nullable=False)
    product_status = Column(Enum('READY','SALE','SOLD_OUT','STOPPED','DELETED'), default='READY')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 4. 파일 공통 관리
class FileAsset(Base):
    __tablename__ = 'file_assets'
    file_id = Column(BigInteger, primary_key=True, autoincrement=True)
    org_id = Column(BigInteger) 
    file_type = Column(Enum('IMAGE','PDF','DOCUMENT','VIDEO','AUDIO','ETC'), nullable=False)
    storage_type = Column(Enum('LOCAL','S3','GCS','NAS','URL'), nullable=False)
    original_file_name = Column(String(500))
    stored_file_name = Column(String(500))
    file_extension = Column(String(30))
    mime_type = Column(String(100))
    file_size = Column(BigInteger, default=0)
    storage_path = Column(String(1000))
    public_url = Column(String(2000))
    thumbnail_url = Column(String(2000))
    checksum_sha256 = Column(String(64))
    active_yn = Column(CHAR(1), default='Y')
    created_at = Column(DateTime, default=datetime.utcnow)

# 5. 상품 이미지 매핑
class ProductImage(Base):
    __tablename__ = 'product_images'
    product_image_id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey('products.product_id'), nullable=False)
    file_id = Column(BigInteger, ForeignKey('file_assets.file_id'), nullable=False)
    image_type = Column(Enum('MAIN','DETAIL','THUMBNAIL','OPTION'), default='DETAIL')
    alt_text = Column(String(500))
    display_order = Column(Integer, default=0)
    active_yn = Column(CHAR(1), default='Y')
    created_at = Column(DateTime, default=datetime.utcnow)

# 6. 상품 첨부파일 (매뉴얼 등)
class ProductFile(Base):
    __tablename__ = 'product_files'
    product_file_id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey('products.product_id'), nullable=False)
    file_id = Column(BigInteger, ForeignKey('file_assets.file_id'), nullable=False)
    file_category = Column(String(50))
    file_description = Column(String(500))
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# 7. 상품 옵션 (SKU)
class ProductVariant(Base):
    __tablename__ = 'product_variants'
    variant_id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey('products.product_id'), nullable=False)
    sku_code = Column(String(100), unique=True, nullable=False)
    option_name1 = Column(String(100))
    option_value1 = Column(String(100))
    option_name2 = Column(String(100))
    option_value2 = Column(String(100))
    additional_price = Column(DECIMAL(15,2), default=0)
    active_yn = Column(CHAR(1), default='Y')

# 8. 지점별 재고
class Inventory(Base):
    __tablename__ = 'inventories'
    inventory_id = Column(BigInteger, primary_key=True, autoincrement=True)
    org_id = Column(BigInteger, nullable=False)
    variant_id = Column(BigInteger, ForeignKey('product_variants.variant_id'), nullable=False)
    stock_quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    safety_stock = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)