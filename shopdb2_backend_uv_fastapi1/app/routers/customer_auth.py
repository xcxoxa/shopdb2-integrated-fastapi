from datetime import datetime, timedelta
import hashlib
import hmac
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.customer_auth import (
    CustomerFindIdRequest,
    CustomerFindIdResponse,
    CustomerLoginRequest,
    CustomerLoginResponse,
    CustomerMessageResponse,
    CustomerProfileUpdate,
    CustomerResetPasswordRequest,
    CustomerResponse,
    CustomerSignupRequest,
)


router = APIRouter(prefix="/api/customer", tags=["고객 회원가입·로그인"])
PBKDF2_ITERATIONS = 260_000


def authenticated_user_id(authorization: str | None, db: Session) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    raw_token = authorization.removeprefix("Bearer ").strip()
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    user_id = db.execute(
        text(
            """
            SELECT user_id
            FROM user_sessions
            WHERE session_token_hash = :token_hash
              AND revoked_at IS NULL
              AND expires_at > CURRENT_TIMESTAMP
            LIMIT 1
            """
        ),
        {"token_hash": token_hash},
    ).scalar_one_or_none()
    if user_id is None:
        raise HTTPException(status_code=401, detail="로그인이 만료되었습니다. 다시 로그인해주세요.")
    return int(user_id)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def save_login_history(
    db: Session,
    request: Request,
    login_id: str,
    result: str,
    user_id: int | None = None,
    reason: str | None = None,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO login_history (
                user_id, login_id_entered, login_result,
                failure_reason, ip_address, user_agent
            ) VALUES (
                :user_id, :login_id, :result,
                :reason, :ip_address, :user_agent
            )
            """
        ),
        {
            "user_id": user_id,
            "login_id": login_id,
            "result": result,
            "reason": reason,
            "ip_address": client_ip(request),
            "user_agent": request.headers.get("user-agent", "")[:500],
        },
    )


@router.post(
    "/signup",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    payload: CustomerSignupRequest,
    db: Session = Depends(get_db),
) -> CustomerResponse:
    login_id = payload.login_id.strip()
    email = payload.email.strip().lower()

    duplicate = db.execute(
        text(
            """
            SELECT user_id
            FROM users
            WHERE login_id = :login_id OR email = :email
            LIMIT 1
            """
        ),
        {"login_id": login_id, "email": email},
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="이미 사용 중인 아이디 또는 이메일입니다.")

    try:
        result = db.execute(
            text(
                """
                INSERT INTO users (
                    org_id, login_id, password_hash, user_name,
                    email, phone, user_status
                ) VALUES (
                    NULL, :login_id, :password_hash, :user_name,
                    :email, :phone, 'ACTIVE'
                )
                """
            ),
            {
                "login_id": login_id,
                "password_hash": hash_password(payload.password),
                "user_name": payload.user_name.strip(),
                "email": email,
                "phone": payload.phone.strip() if payload.phone else None,
            },
        )
        user_id = int(result.lastrowid)

        buyer_role_id = db.execute(
            text("SELECT role_id FROM roles WHERE role_code = 'BUYER' LIMIT 1")
        ).scalar_one_or_none()
        if buyer_role_id is None:
            raise HTTPException(status_code=500, detail="BUYER 권한이 데이터베이스에 없습니다.")

        db.execute(
            text(
                """
                INSERT INTO user_roles (user_id, role_id)
                VALUES (:user_id, :role_id)
                """
            ),
            {"user_id": user_id, "role_id": buyer_role_id},
        )
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="이미 가입된 회원정보입니다.") from error

    return CustomerResponse(
        user_id=user_id,
        login_id=login_id,
        user_name=payload.user_name.strip(),
        email=email,
        phone=payload.phone.strip() if payload.phone else None,
    )


@router.post("/login", response_model=CustomerLoginResponse)
def login(
    payload: CustomerLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> CustomerLoginResponse:
    login_id = payload.login_id.strip()
    row = db.execute(
        text(
            """
            SELECT user_id, login_id, password_hash, user_name,
                   email, phone, user_status
            FROM users
            WHERE login_id = :login_id
            LIMIT 1
            """
        ),
        {"login_id": login_id},
    ).mappings().first()

    if row is None or not verify_password(payload.password, row["password_hash"]):
        save_login_history(db, request, login_id, "FAIL", reason="아이디 또는 비밀번호 불일치")
        db.commit()
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    if row["user_status"] != "ACTIVE":
        save_login_history(db, request, login_id, "FAIL", row["user_id"], "비활성 회원")
        db.commit()
        raise HTTPException(status_code=403, detail="사용할 수 없는 회원 계정입니다.")

    role_code = db.execute(
        text(
            """
            SELECT r.role_code
            FROM user_roles ur
            JOIN roles r ON r.role_id = ur.role_id
            WHERE ur.user_id = :user_id
            ORDER BY CASE r.role_code WHEN 'BUYER' THEN 1 ELSE 2 END
            LIMIT 1
            """
        ),
        {"user_id": row["user_id"]},
    ).scalar_one_or_none() or "BUYER"

    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now() + timedelta(days=7)
    db.execute(
        text(
            """
            INSERT INTO user_sessions (
                user_id, session_token_hash, ip_address, user_agent, expires_at
            ) VALUES (
                :user_id, :token_hash, :ip_address, :user_agent, :expires_at
            )
            """
        ),
        {
            "user_id": row["user_id"],
            "token_hash": token_hash,
            "ip_address": client_ip(request),
            "user_agent": request.headers.get("user-agent", "")[:500],
            "expires_at": expires_at,
        },
    )
    save_login_history(db, request, login_id, "SUCCESS", row["user_id"])
    db.commit()

    return CustomerLoginResponse(
        access_token=raw_token,
        user=CustomerResponse(
            user_id=row["user_id"],
            login_id=row["login_id"],
            user_name=row["user_name"],
            email=row["email"],
            phone=row["phone"],
            role_code=role_code,
        ),
    )


@router.post("/find-id", response_model=CustomerFindIdResponse)
def find_id(
    payload: CustomerFindIdRequest,
    db: Session = Depends(get_db),
) -> CustomerFindIdResponse:
    row = db.execute(
        text(
            """
            SELECT login_id
            FROM users
            WHERE user_name = :user_name
              AND LOWER(email) = :email
              AND user_status = 'ACTIVE'
            LIMIT 1
            """
        ),
        {
            "user_name": payload.user_name.strip(),
            "email": payload.email.strip().lower(),
        },
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="일치하는 회원정보가 없습니다.")
    return CustomerFindIdResponse(login_id=row["login_id"])


@router.post("/reset-password", response_model=CustomerMessageResponse)
def reset_password(
    payload: CustomerResetPasswordRequest,
    db: Session = Depends(get_db),
) -> CustomerMessageResponse:
    user_id = db.execute(
        text(
            """
            SELECT user_id
            FROM users
            WHERE login_id = :login_id
              AND LOWER(email) = :email
              AND user_status = 'ACTIVE'
            LIMIT 1
            """
        ),
        {
            "login_id": payload.login_id.strip(),
            "email": payload.email.strip().lower(),
        },
    ).scalar_one_or_none()
    if user_id is None:
        raise HTTPException(status_code=404, detail="일치하는 회원정보가 없습니다.")

    db.execute(
        text(
            """
            UPDATE users
            SET password_hash = :password_hash
            WHERE user_id = :user_id
            """
        ),
        {
            "password_hash": hash_password(payload.new_password),
            "user_id": user_id,
        },
    )
    db.execute(
        text("DELETE FROM user_sessions WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    db.commit()
    return CustomerMessageResponse(message="비밀번호가 변경되었습니다.")


@router.patch("/profile", response_model=CustomerResponse)
def update_profile(
    payload: CustomerProfileUpdate,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> CustomerResponse:
    user_id = authenticated_user_id(authorization, db)
    email = payload.email.strip().lower()
    duplicate = db.execute(
        text(
            """
            SELECT user_id
            FROM users
            WHERE LOWER(email) = :email AND user_id <> :user_id
            LIMIT 1
            """
        ),
        {"email": email, "user_id": user_id},
    ).scalar_one_or_none()
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="이미 사용 중인 이메일입니다.")

    db.execute(
        text(
            """
            UPDATE users
            SET user_name = :user_name, email = :email, phone = :phone
            WHERE user_id = :user_id
            """
        ),
        {
            "user_name": payload.user_name.strip(),
            "email": email,
            "phone": payload.phone.strip() if payload.phone else None,
            "user_id": user_id,
        },
    )
    row = db.execute(
        text(
            """
            SELECT u.user_id, u.login_id, u.user_name, u.email, u.phone,
                   COALESCE((
                       SELECT r.role_code
                       FROM user_roles ur JOIN roles r ON r.role_id = ur.role_id
                       WHERE ur.user_id = u.user_id
                       ORDER BY CASE r.role_code WHEN 'BUYER' THEN 1 ELSE 2 END
                       LIMIT 1
                   ), 'BUYER') AS role_code
            FROM users u WHERE u.user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).mappings().one()
    db.commit()
    return CustomerResponse(**dict(row))
