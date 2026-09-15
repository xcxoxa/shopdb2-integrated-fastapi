from datetime import datetime

from pydantic import BaseModel, Field


class MenuResponse(BaseModel):
    menu_id: int
    parent_menu_id: int | None = None
    menu_code: str
    menu_name: str
    menu_path: str
    menu_description: str | None = None
    display_order: int
    active_yn: str


class UserMenuResponse(BaseModel):
    menu_id: int
    menu_code: str
    menu_name: str
    menu_path: str
    can_view: str
    can_create: str
    can_update: str
    can_delete: str


class RoleMenuPermissionResponse(BaseModel):
    role_id: int
    role_code: str
    role_name: str
    menu_id: int
    menu_code: str
    menu_name: str
    can_view: str
    can_create: str
    can_update: str
    can_delete: str


class UserSessionCreate(BaseModel):
    user_id: int
    session_token_hash: str = Field(min_length=64, max_length=64)
    ip_address: str | None = Field(default=None, max_length=45)
    user_agent: str | None = Field(default=None, max_length=500)
    expires_at: datetime


class UserSessionResponse(BaseModel):
    session_id: int
    user_id: int
    session_token_hash: str
    ip_address: str | None = None
    user_agent: str | None = None
    expires_at: datetime
    revoked_at: datetime | None = None
    created_at: datetime


class LoginHistoryCreate(BaseModel):
    user_id: int | None = None
    login_id_entered: str | None = Field(default=None, max_length=100)
    login_result: str = Field(pattern="^(SUCCESS|FAIL)$")
    failure_reason: str | None = Field(default=None, max_length=300)
    ip_address: str | None = Field(default=None, max_length=45)
    user_agent: str | None = Field(default=None, max_length=500)


class LoginHistoryResponse(BaseModel):
    login_history_id: int
    user_id: int | None = None
    login_id_entered: str | None = None
    login_result: str
    failure_reason: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    logged_at: datetime


class AccessLogCreate(BaseModel):
    user_id: int | None = None
    menu_id: int | None = None
    http_method: str = Field(min_length=1, max_length=10)
    request_path: str = Field(min_length=1, max_length=500)
    response_status: int = Field(ge=100, le=599)
    ip_address: str | None = Field(default=None, max_length=45)
    response_time_ms: int | None = Field(default=None, ge=0)


class AccessLogResponse(BaseModel):
    access_log_id: int
    user_id: int | None = None
    menu_id: int | None = None
    http_method: str
    request_path: str
    response_status: int
    ip_address: str | None = None
    response_time_ms: int | None = None
    accessed_at: datetime