from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.database import get_db


router = APIRouter(prefix="/api/customer/products", tags=["고객 상품"])


def money(value: Decimal | int | None) -> int:
    return int(value or 0)


@router.get("")
def get_customer_products(db: Session = Depends(get_db)) -> list[dict]:
    product_rows = db.execute(
        text(
            """
            SELECT
                p.product_id,
                p.product_code,
                p.product_name,
                p.short_description,
                p.description,
                p.regular_price,
                p.sale_price,
                p.product_status,
                c.category_name,
                COALESCE(fa.public_url, fa.thumbnail_url) AS image_url
            FROM products p
            JOIN categories c ON c.category_id = p.category_id
            LEFT JOIN categories pc ON pc.category_id = c.parent_category_id
            LEFT JOIN product_images pi
              ON pi.product_id = p.product_id
             AND pi.image_type = 'MAIN'
             AND pi.active_yn = 'Y'
            LEFT JOIN file_assets fa
              ON fa.file_id = pi.file_id
             AND fa.active_yn = 'Y'
            WHERE p.product_status IN ('SALE', 'SOLD_OUT')
              AND c.active_yn = 'Y'
              AND COALESCE(pc.category_name, c.category_name) = '패션'
              AND p.product_code LIKE 'OFFIT%'
            ORDER BY p.created_at DESC, p.product_id DESC
            """
        )
    ).mappings().all()

    if not product_rows:
        return []

    product_ids = [int(row["product_id"]) for row in product_rows]
    variant_rows = db.execute(
        text(
            """
            SELECT
                pv.variant_id,
                pv.product_id,
                pv.sku_code,
                pv.option_name1,
                pv.option_value1,
                pv.option_name2,
                pv.option_value2,
                pv.additional_price,
                COALESCE(SUM(i.stock_quantity), 0) AS stock_quantity,
                COALESCE(SUM(i.reserved_quantity), 0) AS reserved_quantity,
                GREATEST(
                    COALESCE(SUM(i.stock_quantity - i.reserved_quantity), 0),
                    0
                ) AS available_stock
            FROM product_variants pv
            LEFT JOIN inventories i ON i.variant_id = pv.variant_id
            WHERE pv.active_yn = 'Y'
              AND pv.product_id IN :product_ids
            GROUP BY
                pv.variant_id,
                pv.product_id,
                pv.sku_code,
                pv.option_name1,
                pv.option_value1,
                pv.option_name2,
                pv.option_value2,
                pv.additional_price
            ORDER BY pv.product_id, pv.variant_id
            """
        ).bindparams(bindparam("product_ids", expanding=True)),
        {"product_ids": product_ids},
    ).mappings().all()

    variants_by_product: dict[int, list[dict]] = defaultdict(list)
    for row in variant_rows:
        variants_by_product[int(row["product_id"])].append(
            {
                "variant_id": int(row["variant_id"]),
                "sku_code": row["sku_code"],
                "option_name1": row["option_name1"],
                "option_value1": row["option_value1"],
                "option_name2": row["option_name2"],
                "option_value2": row["option_value2"],
                "additional_price": money(row["additional_price"]),
                "stock_quantity": int(row["stock_quantity"] or 0),
                "reserved_quantity": int(row["reserved_quantity"] or 0),
                "available_stock": int(row["available_stock"] or 0),
            }
        )

    result: list[dict] = []
    for row in product_rows:
        product_id = int(row["product_id"])
        variants = variants_by_product[product_id]
        result.append(
            {
                "product_id": product_id,
                "product_code": row["product_code"],
                "product_name": row["product_name"],
                "category_name": row["category_name"],
                "short_description": row["short_description"],
                "description": row["description"],
                "regular_price": money(row["regular_price"]),
                "sale_price": money(row["sale_price"]),
                "product_status": row["product_status"],
                "image_url": row["image_url"],
                "available_stock": sum(item["available_stock"] for item in variants),
                "variants": variants,
            }
        )
    return result
