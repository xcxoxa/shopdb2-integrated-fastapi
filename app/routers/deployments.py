from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db

# 조원 2의 모델과 스키마를 불러옵니다.
from app.models import member2 as models
from app.schemas import member2 as schemas

router = APIRouter(prefix="/api/system", tags=["조원 2 확장 (버전/배포/백업/기능제어)"])

@router.get("/versions", response_model=List[schemas.ApplicationVersionResponse], summary="앱 버전 목록 조회")
def get_versions(db: Session = Depends(get_db)):
    return db.query(models.ApplicationVersion).all()

@router.get("/deployments", response_model=List[schemas.DeploymentHistoryResponse], summary="배포 이력 조회")
def get_deployments(db: Session = Depends(get_db)):
    return db.query(models.DeploymentHistory).all()

@router.get("/backups", response_model=List[schemas.DatabaseBackupHistoryResponse], summary="DB 백업 이력 조회")
def get_backups(db: Session = Depends(get_db)):
    return db.query(models.DatabaseBackupHistory).all()

@router.get("/rollbacks", response_model=List[schemas.RollbackHistoryResponse], summary="롤백 이력 조회")
def get_rollbacks(db: Session = Depends(get_db)):
    return db.query(models.RollbackHistory).all()

@router.get("/feature-flags", response_model=List[schemas.FeatureFlagResponse], summary="피처 플래그 목록 조회")
def get_feature_flags(db: Session = Depends(get_db)):
    return db.query(models.FeatureFlag).all()