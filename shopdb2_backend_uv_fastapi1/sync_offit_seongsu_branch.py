"""Connect seller02 to the branch that owns the six OFFIT fashion products."""

from sqlalchemy import bindparam, text

from app.database import SessionLocal


SELLER_LOGIN_ID = "seller02"
TARGET_ORG_CODE = "OFFIT-SEONGSU"
TARGET_ORG_NAME = "OFFIT 성수점"
OFFIT_PRODUCT_NAMES = (
    "데일리 스니커즈",
    "프린팅 후드티",
    "오버핏 재킷",
    "A라인 롱 스커트",
    "플리츠 미니 스커트",
    "베이지 니트 가디건",
)


def main() -> None:
    db = SessionLocal()
    try:
        seller = db.execute(
            text(
                """
                SELECT user_id, login_id, org_id
                FROM users
                WHERE login_id = :login_id
                LIMIT 1
                """
            ),
            {"login_id": SELLER_LOGIN_ID},
        ).mappings().first()
        if seller is None:
            raise RuntimeError(f"{SELLER_LOGIN_ID} 계정을 찾을 수 없습니다.")

        found_products = db.execute(
            text(
                """
                SELECT product_name
                FROM products
                WHERE product_name IN :product_names
                  AND product_status <> 'DELETED'
                """
            ).bindparams(bindparam("product_names", expanding=True)),
            {"product_names": OFFIT_PRODUCT_NAMES},
        ).scalars().all()
        found_product_names = set(found_products)
        missing_products = [
            name for name in OFFIT_PRODUCT_NAMES if name not in found_product_names
        ]
        if missing_products:
            raise RuntimeError(
                "상품 연결을 변경하지 않았습니다. DB에 없는 OFFIT 상품: "
                + ", ".join(missing_products)
            )

        candidates = db.execute(
            text(
                """
                SELECT
                    ou.org_id,
                    ou.org_code,
                    ou.org_name,
                    COUNT(DISTINCT p.product_name) AS matched_product_count,
                    COALESCE(SUM(i.stock_quantity), 0) AS total_stock
                FROM org_units ou
                JOIN inventories i ON i.org_id = ou.org_id
                JOIN product_variants pv ON pv.variant_id = i.variant_id
                JOIN products p ON p.product_id = pv.product_id
                WHERE p.product_name IN :product_names
                  AND p.product_status <> 'DELETED'
                GROUP BY ou.org_id, ou.org_code, ou.org_name
                HAVING COUNT(DISTINCT p.product_name) = :required_count
                ORDER BY
                    CASE
                        WHEN ou.org_code = :target_code THEN 0
                        WHEN ou.org_name = :target_name THEN 1
                        ELSE 2
                    END,
                    COALESCE(SUM(i.stock_quantity), 0) DESC,
                    ou.org_id
                """
            ).bindparams(bindparam("product_names", expanding=True)),
            {
                "product_names": OFFIT_PRODUCT_NAMES,
                "required_count": len(OFFIT_PRODUCT_NAMES),
                "target_code": TARGET_ORG_CODE,
                "target_name": TARGET_ORG_NAME,
            },
        ).mappings().all()
        if not candidates:
            raise RuntimeError(
                "여섯 OFFIT 상품을 모두 보유한 지사를 찾지 못했습니다. "
                "기존 재고 데이터는 변경하지 않았습니다."
            )

        branch = candidates[0]
        target_org_id = int(branch["org_id"])

        code_owner = db.execute(
            text(
                """
                SELECT org_id
                FROM org_units
                WHERE org_code = :org_code
                LIMIT 1
                """
            ),
            {"org_code": TARGET_ORG_CODE},
        ).scalar_one_or_none()
        target_code = (
            TARGET_ORG_CODE
            if code_owner is None or int(code_owner) == target_org_id
            else str(branch["org_code"])
        )

        db.execute(
            text(
                """
                UPDATE org_units
                SET org_code = :org_code,
                    org_name = :org_name,
                    org_type = 'BRANCH',
                    active_yn = 'Y'
                WHERE org_id = :org_id
                """
            ),
            {
                "org_code": target_code,
                "org_name": TARGET_ORG_NAME,
                "org_id": target_org_id,
            },
        )
        db.execute(
            text("UPDATE users SET org_id = :org_id WHERE user_id = :user_id"),
            {"org_id": target_org_id, "user_id": int(seller["user_id"])},
        )
        db.execute(
            text(
                """
                UPDATE seller_profiles
                SET company_name = :company_name
                WHERE user_id = :user_id
                """
            ),
            {
                "company_name": TARGET_ORG_NAME,
                "user_id": int(seller["user_id"]),
            },
        )
        db.execute(
            text("DELETE FROM user_sessions WHERE user_id = :user_id"),
            {"user_id": int(seller["user_id"])},
        )
        db.commit()

        print("OFFIT 성수점 연결 완료")
        print(f"- 로그인 ID: {SELLER_LOGIN_ID}")
        print(f"- 조직 ID: {target_org_id}")
        print(f"- 지사명: {TARGET_ORG_NAME}")
        print(f"- 연결 상품: {len(OFFIT_PRODUCT_NAMES)}개")
        print(f"- 재고 합계: {int(branch['total_stock'])}개")
        print("기존 세션을 종료했습니다. seller02로 다시 로그인해주세요.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
