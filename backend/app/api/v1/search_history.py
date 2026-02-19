from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.search_history import SearchHistory

router = APIRouter(prefix="/search-history", tags=["search-history"])

@router.get("/")
def get_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(SearchHistory)
        .filter(SearchHistory.user_id == user.id)
        .order_by(SearchHistory.created_at.desc())
        .limit(50)
        .all()
    )
