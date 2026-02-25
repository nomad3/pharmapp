from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.site_setting import SiteSetting
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["settings"])

BANK_KEYS = [
    "bank_name", "bank_account_type", "bank_account_number",
    "bank_rut", "bank_holder_name", "bank_email",
]


@router.get("/bank-details")
def get_bank_details(db: Session = Depends(get_db)):
    """Public endpoint — needed at checkout and order detail."""
    rows = db.query(SiteSetting).filter(SiteSetting.key.in_(BANK_KEYS)).all()
    return {row.key: row.value for row in rows}


class BankDetailsUpdate(BaseModel):
    bank_name: str = ""
    bank_account_type: str = ""
    bank_account_number: str = ""
    bank_rut: str = ""
    bank_holder_name: str = ""
    bank_email: str = ""


@router.put("/bank-details")
def update_bank_details(
    body: BankDetailsUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Admin-only — update bank transfer details."""
    for key in BANK_KEYS:
        value = getattr(body, key, "")
        existing = db.query(SiteSetting).filter(SiteSetting.key == key).first()
        if existing:
            existing.value = value
        else:
            db.add(SiteSetting(key=key, value=value))
    db.commit()
    return {"status": "ok"}
