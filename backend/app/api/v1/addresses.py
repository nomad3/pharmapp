from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.delivery_address import DeliveryAddress
from app.schemas.address import AddressCreate, AddressOut

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("/", response_model=list[AddressOut])
def list_addresses(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(DeliveryAddress).filter(DeliveryAddress.user_id == user.id).all()


@router.post("/", response_model=AddressOut)
def create_address(
    body: AddressCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    addr = DeliveryAddress(
        user_id=user.id,
        label=body.label,
        address=body.address,
        comuna=body.comuna,
        instructions=body.instructions,
    )
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


@router.delete("/{address_id}")
def delete_address(
    address_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    addr = db.query(DeliveryAddress).filter(
        DeliveryAddress.id == address_id,
        DeliveryAddress.user_id == user.id,
    ).first()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(addr)
    db.commit()
    return {"status": "deleted"}
