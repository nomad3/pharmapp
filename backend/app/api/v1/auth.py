from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import generate_otp, create_access_token
from app.models.user import User
from app.models.otp import OtpCode
from app.schemas.auth import OtpRequest, OtpVerify, Token
from app.services import whatsapp

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/otp/request")
async def request_otp(body: OtpRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == body.phone_number).first()
    if not user:
        user = User(phone_number=body.phone_number)
        db.add(user)
        db.commit()
        db.refresh(user)

    code = generate_otp()
    otp = OtpCode(
        user_id=user.id,
        code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    db.add(otp)
    db.commit()

    try:
        await whatsapp.send_otp(body.phone_number, code)
    except Exception:
        pass  # Log already handled in client; don't block auth if ST is down

    return {"message": "OTP sent via WhatsApp"}

@router.post("/otp/verify", response_model=Token)
def verify_otp(body: OtpVerify, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == body.phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = (
        db.query(OtpCode)
        .filter(
            OtpCode.user_id == user.id,
            OtpCode.code == body.code,
            OtpCode.verified == False,
            OtpCode.expires_at > datetime.now(timezone.utc),
        )
        .order_by(OtpCode.created_at.desc())
        .first()
    )
    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    otp.verified = True
    db.commit()

    token = create_access_token(str(user.id))
    return Token(access_token=token)


@router.post("/refresh")
def refresh_token(user: User = Depends(get_current_user)):
    """Issue a new JWT if the current one is still valid."""
    new_token = create_access_token(str(user.id))
    return {"access_token": new_token}


@router.get("/profile")
def get_profile(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "phone_number": user.phone_number,
        "name": user.name,
        "comuna": user.comuna,
        "notification_prefs": user.notification_prefs or {
            "order_updates": True,
            "price_alerts": True,
            "refill_reminders": True,
            "promotions": False,
        },
        "created_at": str(user.created_at),
    }


@router.put("/profile")
def update_profile(
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if "name" in body:
        user.name = body["name"]
    if "comuna" in body:
        user.comuna = body["comuna"]
    if "notification_prefs" in body:
        user.notification_prefs = body["notification_prefs"]
    db.commit()
    return {"status": "updated"}
