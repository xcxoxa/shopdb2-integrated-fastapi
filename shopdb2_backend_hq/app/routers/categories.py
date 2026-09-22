from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import member2 as models
from app.schemas import member2 as schemas

router = APIRouter(prefix="/api/categories", tags=["조원 2 카테고리"])

@router.get("", response_model=List[schemas.CategoryResponse], summary="카테고리 목록 조회")
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()