"""Reset the three demo accounts to a known local-development password."""

from sqlalchemy import bindparam, text

from app.database import SessionLocal
from app.routers.customer_auth import hash_password


DEMO_LOGIN_IDS = ("admin01", "seller02", "buyer03")
DEMO_PASSWORD = "offit1234"


def main() -> None:
    db = SessionLocal()
    try:
        users = db.execute(
            text(
                """
                SELECT user_id, login_id
                FROM users
                WHERE login_id IN :login_ids
                """
            ).bindparams(bindparam("login_ids", expanding=True)),
            {"login_ids": DEMO_LOGIN_IDS},
        ).mappings().all()

        found_ids = {str(user["login_id"]) for user in users}
        missing_ids = [login_id for login_id in DEMO_LOGIN_IDS if login_id not in found_ids]
        if missing_ids:
            raise RuntimeError(
                "비밀번호를 변경하지 않았습니다. 존재하지 않는 계정: "
                + ", ".join(missing_ids)
            )

        for login_id in DEMO_LOGIN_IDS:
            db.execute(
                text(
                    """
                    UPDATE users
                    SET password_hash = :password_hash
                    WHERE login_id = :login_id
                    """
                ),
                {
                    "login_id": login_id,
                    "password_hash": hash_password(DEMO_PASSWORD),
                },
            )

        user_ids = [int(user["user_id"]) for user in users]
        db.execute(
            text(
                """
                DELETE FROM user_sessions
                WHERE user_id IN :user_ids
                """
            ).bindparams(bindparam("user_ids", expanding=True)),
            {"user_ids": user_ids},
        )
        db.commit()

        print("테스트 계정 비밀번호 초기화 완료")
        for login_id in DEMO_LOGIN_IDS:
            print(f"- {login_id} / {DEMO_PASSWORD}")
        print("기존 로그인 세션도 모두 종료했습니다.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
