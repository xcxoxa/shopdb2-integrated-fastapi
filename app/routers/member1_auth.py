from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.member1_auth import (
    AccessLogCreate,
    AccessLogResponse,
    LoginHistoryCreate,
    LoginHistoryResponse,
    MenuResponse,
    RoleMenuPermissionResponse,
    UserMenuResponse,
    UserSessionCreate,
    UserSessionResponse,
)


router = APIRouter(
    prefix="/api/member1",
    tags=["조원 1 메뉴·권한·접속 관리"],
)


@router.get("/menus", response_model=list[MenuResponse])
def get_menus(
    db: Session = Depends(get_db),
) -> list[MenuResponse]:
    query = text(
        """
        SELECT
            menu_id,
            parent_menu_id,
            menu_code,
            menu_name,
            menu_path,
            menu_description,
            display_order,
            active_yn
        FROM menus
        ORDER BY display_order, menu_id
        """
    )

    rows = db.execute(query).mappings().all()
    return [MenuResponse(**row) for row in rows]


@router.get(
    "/users/{user_id}/menus",
    response_model=list[UserMenuResponse],
)
def get_user_menus(
    user_id: int,
    db: Session = Depends(get_db),
) -> list[UserMenuResponse]:
    user_exists = db.execute(
        text(
            """
            SELECT user_id
            FROM users
            WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).first()

    if user_exists is None:
        raise HTTPException(
            status_code=404,
            detail="회원을 찾을 수 없습니다.",
        )

    query = text(
        """
        SELECT DISTINCT
            m.menu_id,
            m.menu_code,
            m.menu_name,
            m.menu_path,
            rmp.can_view,
            rmp.can_create,
            rmp.can_update,
            rmp.can_delete
        FROM user_roles ur
        JOIN role_menu_permissions rmp
            ON ur.role_id = rmp.role_id
        JOIN menus m
            ON rmp.menu_id = m.menu_id
        WHERE ur.user_id = :user_id
          AND rmp.can_view = 'Y'
          AND m.active_yn = 'Y'
        ORDER BY m.display_order, m.menu_id
        """
    )

    rows = db.execute(
        query,
        {"user_id": user_id},
    ).mappings().all()

    return [UserMenuResponse(**row) for row in rows]


@router.get(
    "/role-menu-permissions",
    response_model=list[RoleMenuPermissionResponse],
)
def get_role_menu_permissions(
    db: Session = Depends(get_db),
) -> list[RoleMenuPermissionResponse]:
    query = text(
        """
        SELECT
            r.role_id,
            r.role_code,
            r.role_name,
            m.menu_id,
            m.menu_code,
            m.menu_name,
            rmp.can_view,
            rmp.can_create,
            rmp.can_update,
            rmp.can_delete
        FROM role_menu_permissions rmp
        JOIN roles r
            ON rmp.role_id = r.role_id
        JOIN menus m
            ON rmp.menu_id = m.menu_id
        ORDER BY r.role_id, m.display_order, m.menu_id
        """
    )

    rows = db.execute(query).mappings().all()
    return [RoleMenuPermissionResponse(**row) for row in rows]


@router.post(
    "/sessions",
    response_model=UserSessionResponse,
    status_code=201,
)
def create_user_session(
    payload: UserSessionCreate,
    db: Session = Depends(get_db),
) -> UserSessionResponse:
    query = text(
        """
        INSERT INTO user_sessions (
            user_id,
            session_token_hash,
            ip_address,
            user_agent,
            expires_at
        )
        VALUES (
            :user_id,
            :session_token_hash,
            :ip_address,
            :user_agent,
            :expires_at
        )
        """
    )

    try:
        db.execute(query, payload.model_dump())
        session_id = db.execute(
            text("SELECT LAST_INSERT_ID()")
        ).scalar_one()
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="회원이 없거나 세션 토큰이 중복되었습니다.",
        )

    row = db.execute(
        text(
            """
            SELECT
                session_id,
                user_id,
                session_token_hash,
                ip_address,
                user_agent,
                expires_at,
                revoked_at,
                created_at
            FROM user_sessions
            WHERE session_id = :session_id
            """
        ),
        {"session_id": session_id},
    ).mappings().first()

    return UserSessionResponse(**row)


@router.post(
    "/login-history",
    response_model=LoginHistoryResponse,
    status_code=201,
)
def create_login_history(
    payload: LoginHistoryCreate,
    db: Session = Depends(get_db),
) -> LoginHistoryResponse:
    query = text(
        """
        INSERT INTO login_history (
            user_id,
            login_id_entered,
            login_result,
            failure_reason,
            ip_address,
            user_agent

        )
        VALUES (
            :user_id,
            :login_id_entered,
            :login_result,
            :failure_reason,
            :ip_address,
            :user_agent
        )
        """
    )

    try:
        db.execute(query, payload.model_dump())
        login_history_id = db.execute(
            text("SELECT LAST_INSERT_ID()")
        ).scalar_one()
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="존재하지 않는 회원 번호입니다.",
        )

    row = db.execute(
        text(
            """
            SELECT
                login_history_id,
                user_id,
                login_id_entered,
                login_result,
                failure_reason,
                ip_address,
                user_agent,
                logged_at
            FROM login_history
            WHERE login_history_id = :login_history_id
            """
        ),
        {"login_history_id": login_history_id},
    ).mappings().first()

    return LoginHistoryResponse(**row)


@router.get(
    "/login-history",
    response_model=list[LoginHistoryResponse],
)
def get_login_history(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[LoginHistoryResponse]:
    query = text(
        """
        SELECT
            login_history_id,
            user_id,
            login_id_entered,
            login_result,
            failure_reason,
            ip_address,
            user_agent,
            logged_at
        FROM login_history
        ORDER BY logged_at DESC, login_history_id DESC
        LIMIT :limit
        """
    )

    rows = db.execute(
        query,
        {"limit": limit},
    ).mappings().all()

    return [LoginHistoryResponse(**row) for row in rows]


@router.post(
    "/access-logs",
    response_model=AccessLogResponse,
    status_code=201,
)
def create_access_log(
    payload: AccessLogCreate,
    db: Session = Depends(get_db),
) -> AccessLogResponse:
    query = text(
        """
        INSERT INTO access_logs (
            user_id,
            menu_id,
            http_method,
            request_path,
            response_status,
            ip_address,
            response_time_ms
        )
        VALUES (
            :user_id,
            :menu_id,
            :http_method,
            :request_path,
            :response_status,
            :ip_address,
            :response_time_ms
        )
        """
    )

    values = payload.model_dump()
    values["http_method"] = values["http_method"].upper()

    try:
        db.execute(query, values)
        access_log_id = db.execute(
            text("SELECT LAST_INSERT_ID()")
        ).scalar_one()
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="회원 번호 또는 메뉴 번호가 올바르지 않습니다.",
        )

    row = db.execute(
        text(
            """
            SELECT
                access_log_id,
                user_id,
                menu_id,
                http_method,
                request_path,
                response_status,
                ip_address,
                response_time_ms,
                accessed_at
            FROM access_logs
            WHERE access_log_id = :access_log_id
            """
        ),
        {"access_log_id": access_log_id},
    ).mappings().first()

    return AccessLogResponse(**row)