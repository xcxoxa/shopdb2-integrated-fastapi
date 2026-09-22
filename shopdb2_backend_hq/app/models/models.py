from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CHAR,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base
# ==========================================
# [확장 프로젝트] 조원 2 담당: 버전·배포·백업·롤백
# ==========================================

class ApplicationVersion(Base):
    __tablename__ = 'application_versions'
    version_id = Column(BigInteger, primary_key=True, autoincrement=True)
    version_name = Column(String(50), nullable=False, unique=True)
    git_commit_hash = Column(String(64), nullable=False)
    release_notes = Column(Text)
    version_status = Column(Enum('DEVELOPMENT', 'STAGING', 'PRODUCTION', 'ROLLED_BACK', 'ARCHIVED'), default='DEVELOPMENT', nullable=False)
    created_by_user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class DeploymentHistory(Base):
    __tablename__ = 'deployment_history'
    deployment_id = Column(BigInteger, primary_key=True, autoincrement=True)
    version_id = Column(BigInteger, ForeignKey('application_versions.version_id'), nullable=False)
    environment_type = Column(Enum('LOCAL', 'DEVELOPMENT', 'STAGING', 'PRODUCTION'), nullable=False)
    deployment_status = Column(Enum('READY', 'RUNNING', 'SUCCESS', 'FAILED', 'CANCELLED'), default='READY', nullable=False)
    deployed_by_user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    deployment_message = Column(String(1000))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class DatabaseBackupHistory(Base):
    __tablename__ = 'database_backup_history'
    backup_id = Column(BigInteger, primary_key=True, autoincrement=True)
    version_id = Column(BigInteger, ForeignKey('application_versions.version_id'))
    backup_name = Column(String(150), nullable=False, unique=True)
    backup_type = Column(Enum('FULL', 'SCHEMA_ONLY', 'DATA_ONLY'), default='FULL', nullable=False)
    storage_path = Column(String(500), nullable=False)
    checksum_sha256 = Column(CHAR(64))
    file_size_bytes = Column(BigInteger)
    backup_status = Column(Enum('RUNNING', 'SUCCESS', 'FAILED', 'DELETED'), default='RUNNING', nullable=False)
    created_by_user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)

class RollbackHistory(Base):
    __tablename__ = 'rollback_history'
    rollback_id = Column(BigInteger, primary_key=True, autoincrement=True)
    from_version_id = Column(BigInteger, ForeignKey('application_versions.version_id'), nullable=False)
    to_version_id = Column(BigInteger, ForeignKey('application_versions.version_id'), nullable=False)
    deployment_id = Column(BigInteger, ForeignKey('deployment_history.deployment_id'))
    backup_id = Column(BigInteger, ForeignKey('database_backup_history.backup_id'))
    rollback_reason = Column(String(1000), nullable=False)
    rollback_status = Column(Enum('READY', 'RUNNING', 'SUCCESS', 'FAILED'), default='READY', nullable=False)
    requested_by_user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    approved_by_user_id = Column(BigInteger, ForeignKey('users.user_id'))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class FeatureFlag(Base):
    __tablename__ = 'feature_flags'
    feature_flag_id = Column(BigInteger, primary_key=True, autoincrement=True)
    flag_code = Column(String(100), nullable=False, unique=True)
    flag_name = Column(String(150), nullable=False)
    description = Column(String(1000))
    enabled_yn = Column(CHAR(1), default='N', nullable=False)
    target_role_code = Column(String(30))
    start_at = Column(DateTime)
    end_at = Column(DateTime)
    updated_by_user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
# from .database import Base (기존 파일 상단에 이미 Base가 임포트되어 있을 것입니다)

class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True)
    target_name = Column(String(100), nullable=False, comment="대상 (지사/파트너명)")
    period = Column(String(50), nullable=False, comment="정산 기간 (예: 2026-08-01 ~ 2026-08-31)")
    total_sales = Column(Integer, nullable=False, default=0, comment="총 매출액")
    commission = Column(Integer, nullable=False, default=0, comment="본사 수수료")
    final_amount = Column(Integer, nullable=False, default=0, comment="최종 지급액")
    status = Column(String(20), nullable=False, default="정산대기", comment="상태 (정산대기/지급완료)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일시")








