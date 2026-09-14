from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import member2 as models
from app.schemas import member2 as schemas

router = APIRouter(prefix="/api/sellers", tags=["조원 2 판매자"])

@router.get("", response_model=List[schemas.SellerProfileResponse], summary="판매자 프로필 목록 조회")
def get_sellers(db: Session = Depends(get_db)):
    return db.query(models.SellerProfile).all()