from datetime import datetime, timedelta
import hashlib
import hmac
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db


router = APIRouter(prefix="/api/auth", tags=["통합 로그인·권한"])

HQ_ROLES = {"ADMIN", "HQ", "HEADQUARTER", "HQ_ADMIN", "SUPER_ADMIN"}
BRANCH_ROLES = {"SELLER", "BRANCH", "BRANCH_ADMIN", "BRANCH_MANAGER"}
CUSTOMER_ROLES = {"BUYER", "CUSTOMER", "MEMBER", "USER"}


class UnifiedLoginRequest(BaseModel):
    login_id: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=100)


class UnifiedUserResponse(BaseModel):
    user_id: int
    login_id: str
    user_name: str
    email: str | None = None
    role_code: str
    destination: str
    org_id: int | None = None
    org_name: str | None = None


class UnifiedLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UnifiedUserResponse


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False

    stored_hash = str(stored_hash)
    try:
        algorithm, iterations, salt, expected = stored_hash.split("$", 3)
        if algorithm == "pbkdf2_sha256":
            actual = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                int(iterations),
            ).hex()
            return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        pass

    if stored_hash.startswith("{SHA256}"):
        actual = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(stored_hash[8:].lower(), actual)

    if len(stored_hash) == 64 and all(c in "0123456789abcdefABCDEF" for c in stored_hash):
        actual = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(stored_hash.lower(), actual)

    # 기존 실습 데이터의 평문 비밀번호 호환용입니다.
    return hmac.compare_digest(stored_hash, password)


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()[:45]
    return request.client.host[:45] if request.client else None


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


def role_destination(role_codes: list[str]) -> tuple[str, str]:
    normalized = [code.upper() for code in role_codes]
    for code in normalized:
        if code in HQ_ROLES:
            return code, "HEADQUARTER"
    for code in normalized:
        if code in BRANCH_ROLES:
            return code, "BRANCH"
    for code in normalized:
        if code in CUSTOMER_ROLES:
            return code, "CUSTOMER"
    raise HTTPException(status_code=403, detail="접속 가능한 권한이 없습니다.")


def find_org(db: Session, org_id: int | None, destination: str) -> dict | None:
    if destination == "CUSTOMER":
        return None

    if org_id is not None:
        row = db.execute(
            text(
                "SELECT org_id, org_name, org_type FROM org_units "
                "WHERE org_id = :org_id AND active_yn = 'Y' LIMIT 1"
            ),
            {"org_id": org_id},
        ).mappings().first()
        if row:
            return dict(row)

    org_type = "HEADQUARTER" if destination == "HEADQUARTER" else "BRANCH"
    row = db.execute(
        text(
            "SELECT org_id, org_name, org_type FROM org_units "
            "WHERE org_type = :org_type AND active_yn = 'Y' ORDER BY org_id LIMIT 1"
        ),
        {"org_type": org_type},
    ).mappings().first()
    return dict(row) if row else None


@router.post("/login", response_model=UnifiedLoginResponse)
def login(
    payload: UnifiedLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> UnifiedLoginResponse:
    login_id = payload.login_id.strip()
    row = db.execute(
        text(
            """
            SELECT u.user_id, u.org_id, u.login_id, u.password_hash,
                   u.user_name, u.email, u.user_status,
                   GROUP_CONCAT(DISTINCT r.role_code ORDER BY r.role_id SEPARATOR ',') AS roles
            FROM users u
            LEFT JOIN user_roles ur ON ur.user_id = u.user_id
            LEFT JOIN roles r ON r.role_id = ur.role_id
            WHERE u.login_id = :login_id
            GROUP BY u.user_id, u.org_id, u.login_id, u.password_hash,
                     u.user_name, u.email, u.user_status
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
        raise HTTPException(status_code=403, detail="사용할 수 없는 계정입니다.")

    role_codes = [code for code in str(row["roles"] or "").split(",") if code]
    role_code, destination = role_destination(role_codes)
    org = find_org(db, row["org_id"], destination)
    if destination != "CUSTOMER" and org is None:
        save_login_history(db, request, login_id, "FAIL", row["user_id"], "활성 조직 없음")
        db.commit()
        raise HTTPException(status_code=403, detail="활성 조직 정보를 찾을 수 없습니다.")

    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now() + timedelta(hours=8)
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

    return UnifiedLoginResponse(
        access_token=raw_token,
        expires_at=expires_at,
        user=UnifiedUserResponse(
            user_id=row["user_id"],
            login_id=row["login_id"],
            user_name=row["user_name"],
            email=row["email"],
            role_code=role_code,
            destination=destination,
            org_id=org["org_id"] if org else None,
            org_name=org["org_name"] if org else None,
        ),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    raw_token = authorization.removeprefix("Bearer ").strip()
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    db.execute(
        text(
            "UPDATE user_sessions SET revoked_at = CURRENT_TIMESTAMP "
            "WHERE session_token_hash = :token_hash AND revoked_at IS NULL"
        ),
        {"token_hash": token_hash},
    )
    db.commit()
