from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.user_favorite import UserFavorite
from app.schemas.favorite import FavoriteCreate, FavoriteOut

router = APIRouter(prefix="/favorites", tags=["favorites"])

@router.get("/", response_model=list[FavoriteOut])
def list_favorites(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(UserFavorite).filter(UserFavorite.user_id == user.id).all()

@router.post("/", response_model=FavoriteOut, status_code=201)
def add_favorite(body: FavoriteCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    fav = UserFavorite(user_id=user.id, medication_id=body.medication_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav

@router.delete("/{favorite_id}", status_code=204)
def remove_favorite(favorite_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    fav = db.query(UserFavorite).filter(UserFavorite.id == favorite_id, UserFavorite.user_id == user.id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(fav)
    db.commit()
