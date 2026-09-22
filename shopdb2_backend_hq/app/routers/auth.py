from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.schemas.member1_auth import (
    UnifiedLoginRequest,
    UnifiedLoginResponse,
    UnifiedUserResponse,
)


router = APIRouter(prefix="/api/auth", tags=["통합 로그인·권한"])

HQ_ROLES = {"ADMIN", "HQ", "HEADQUARTER", "HQ_ADMIN", "SUPER_ADMIN"}
BRANCH_ROLES = {"SELLER", "BRANCH", "BRANCH_ADMIN", "BRANCH_MANAGER"}
CUSTOMER_ROLES = {"BUYER", "CUSTOMER", "MEMBER", "USER"}


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()[:45]
    return request.client.host[:45] if request.client else None


def _table_columns(table_name: str) -> set[str]:
    try:
        return {column["name"] for column in inspect(engine).get_columns(table_name)}
    except Exception:
        return set()


def _verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False

    stored = str(stored)
    encoded = password.encode("utf-8")

    if stored.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return bcrypt.checkpw(encoded, stored.encode("utf-8"))
        except ValueError:
            return False

    if stored.startswith("{SHA256}"):
        expected = hashlib.sha256(encoded).hexdigest()
        return hmac.compare_digest(stored[8:].lower(), expected)

    if len(stored) == 64 and all(character in "0123456789abcdefABCDEF" for character in stored):
        expected = hashlib.sha256(encoded).hexdigest()
        return hmac.compare_digest(stored.lower(), expected)

    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, digest = stored.split("$", 3)
            expected = hashlib.pbkdf2_hmac(
                "sha256", encoded, salt.encode("utf-8"), int(iterations)
            ).hex()
            return hmac.compare_digest(digest, expected)
        except (TypeError, ValueError):
            return False

    # 기존 실습 DB에서 평문 비밀번호를 사용한 경우만 호환합니다.
    return hmac.compare_digest(stored, password)


def _role_destination(role_codes: list[str]) -> tuple[str, str]:
    normalized = [role.upper() for role in role_codes]
    for role in normalized:
        if role in HQ_ROLES:
            return role, "HEADQUARTER"
    for role in normalized:
        if role in BRANCH_ROLES:
            return role, "BRANCH"
    for role in normalized:
        if role in CUSTOMER_ROLES:
            return role, "CUSTOMER"
    raise HTTPException(status_code=403, detail="접속 가능한 권한이 없습니다.")


def _find_org(db: Session, user_id: int, destination: str) -> dict | None:
    if destination == "CUSTOMER":
        return None

    users_columns = _table_columns("users")
    user_roles_columns = _table_columns("user_roles")
    org_id = None

    if "org_id" in users_columns:
        org_id = db.execute(
            text("SELECT org_id FROM users WHERE user_id = :user_id"),
            {"user_id": user_id},
        ).scalar()
    elif "org_id" in user_roles_columns:
        org_id = db.execute(
            text(
                "SELECT org_id FROM user_roles "
                "WHERE user_id = :user_id AND org_id IS NOT NULL LIMIT 1"
            ),
            {"user_id": user_id},
        ).scalar()

    org_type = "HEADQUARTER" if destination == "HEADQUARTER" else "BRANCH"
    if org_id is not None:
        row = db.execute(
            text(
                "SELECT org_id, org_name, org_type FROM org_units "
                "WHERE org_id = :org_id AND active_yn = 'Y'"
            ),
            {"org_id": org_id},
        ).mappings().first()
    else:
        row = db.execute(
            text(
                "SELECT org_id, org_name, org_type FROM org_units "
                "WHERE org_type = :org_type AND active_yn = 'Y' ORDER BY org_id LIMIT 1"
            ),
            {"org_type": org_type},
        ).mappings().first()

    return dict(row) if row else None


def _record_login(
    db: Session,
    request: Request,
    login_id: str,
    result: str,
    user_id: int | None = None,
    reason: str | None = None,
) -> None:
    db.execute(
        text(
            "INSERT INTO login_history "
            "(user_id, login_id_entered, login_result, failure_reason, ip_address, user_agent) "
            "VALUES (:user_id, :login_id, :result, :reason, :ip, :agent)"
        ),
        {
            "user_id": user_id,
            "login_id": login_id,
            "result": result,
            "reason": reason,
            "ip": _client_ip(request),
            "agent": request.headers.get("user-agent", "")[:500],
        },
    )


def _record_access(
    db: Session,
    request: Request,
    response_status: int,
    user_id: int | None = None,
) -> None:
    db.execute(
        text(
            "INSERT INTO access_logs "
            "(user_id, menu_id, http_method, request_path, response_status, ip_address, response_time_ms) "
            "VALUES (:user_id, NULL, 'POST', '/api/auth/login', :status, :ip, 0)"
        ),
        {"user_id": user_id, "status": response_status, "ip": _client_ip(request)},
    )


@router.post("/login", response_model=UnifiedLoginResponse)
def unified_login(
    payload: UnifiedLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> UnifiedLoginResponse:
    login_id = payload.login_id.strip()
    row = db.execute(
        text(
            "SELECT u.user_id, u.login_id, u.user_name, u.email, "
            "u.password_hash, u.user_status, "
            "GROUP_CONCAT(DISTINCT r.role_code ORDER BY r.role_id SEPARATOR ',') AS roles "
            "FROM users u "
            "LEFT JOIN user_roles ur ON ur.user_id = u.user_id "
            "LEFT JOIN roles r ON r.role_id = ur.role_id "
            "WHERE u.login_id = :login_id "
            "GROUP BY u.user_id, u.login_id, u.user_name, u.email, "
            "u.password_hash, u.user_status"
        ),
        {"login_id": login_id},
    ).mappings().first()

    if row is None or not _verify_password(payload.password, row.get("password_hash")):
        _record_login(db, request, login_id, "FAIL", reason="INVALID_CREDENTIALS")
        _record_access(db, request, 401)
        db.commit()
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 일치하지 않습니다.")

    if str(row.get("user_status", "ACTIVE")).upper() != "ACTIVE":
        _record_login(db, request, login_id, "FAIL", row["user_id"], "INACTIVE_USER")
        _record_access(db, request, 403, row["user_id"])
        db.commit()
        raise HTTPException(status_code=403, detail="사용할 수 없는 계정입니다.")

    roles = [role for role in str(row.get("roles") or "").split(",") if role]
    role_code, destination = _role_destination(roles)
    org = _find_org(db, row["user_id"], destination)

    if destination in {"HEADQUARTER", "BRANCH"} and org is None:
        _record_login(db, request, login_id, "FAIL", row["user_id"], "ORG_NOT_FOUND")
        _record_access(db, request, 403, row["user_id"])
        db.commit()
        raise HTTPException(status_code=403, detail="활성 조직 정보를 찾을 수 없습니다.")

    token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires_at = datetime.now() + timedelta(hours=8)

    db.execute(
        text(
            "INSERT INTO user_sessions "
            "(user_id, session_token_hash, ip_address, user_agent, expires_at) "
            "VALUES (:user_id, :token_hash, :ip, :agent, :expires_at)"
        ),
        {
            "user_id": row["user_id"],
            "token_hash": token_hash,
            "ip": _client_ip(request),
            "agent": request.headers.get("user-agent", "")[:500],
            "expires_at": expires_at,
        },
    )
    _record_login(db, request, login_id, "SUCCESS", row["user_id"])
    _record_access(db, request, 200, row["user_id"])
    db.commit()

    return UnifiedLoginResponse(
        access_token=token,
        expires_at=expires_at,
        user=UnifiedUserResponse(
            user_id=row["user_id"],
            login_id=row["login_id"],
            user_name=row["user_name"],
            email=row.get("email"),
            role_code=role_code,
            destination=destination,
            org_id=org.get("org_id") if org else None,
            org_name=org.get("org_name") if org else None,
        ),
    )


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return authorization.split(" ", 1)[1].strip()


@router.get("/me", response_model=UnifiedUserResponse)
def current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> UnifiedUserResponse:
    token_hash = hashlib.sha256(_bearer_token(authorization).encode("utf-8")).hexdigest()
    row = db.execute(
        text(
            "SELECT u.user_id, u.login_id, u.user_name, u.email, "
            "GROUP_CONCAT(DISTINCT r.role_code ORDER BY r.role_id SEPARATOR ',') AS roles "
            "FROM user_sessions s "
            "JOIN users u ON u.user_id = s.user_id "
            "LEFT JOIN user_roles ur ON ur.user_id = u.user_id "
            "LEFT JOIN roles r ON r.role_id = ur.role_id "
            "WHERE s.session_token_hash = :token_hash AND s.revoked_at IS NULL "
            "AND s.expires_at > NOW() GROUP BY u.user_id, u.login_id, u.user_name, u.email"
        ),
        {"token_hash": token_hash},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다.")

    roles = [role for role in str(row.get("roles") or "").split(",") if role]
    role_code, destination = _role_destination(roles)
    org = _find_org(db, row["user_id"], destination)
    return UnifiedUserResponse(
        user_id=row["user_id"],
        login_id=row["login_id"],
        user_name=row["user_name"],
        email=row.get("email"),
        role_code=role_code,
        destination=destination,
        org_id=org.get("org_id") if org else None,
        org_name=org.get("org_name") if org else None,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> None:
    token_hash = hashlib.sha256(_bearer_token(authorization).encode("utf-8")).hexdigest()
    db.execute(
        text(
            "UPDATE user_sessions SET revoked_at = NOW() "
            "WHERE session_token_hash = :token_hash AND revoked_at IS NULL"
        ),
        {"token_hash": token_hash},
    )
    db.commit()
