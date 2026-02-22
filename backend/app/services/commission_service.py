import logging
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.commission import Commission, CommissionStatus
from app.models.pharmacy_partner import PharmacyPartner

logger = logging.getLogger(__name__)


def record_commission(db: Session, order: Order):
    existing = db.query(Commission).filter(Commission.order_id == order.id).first()
    if existing:
        return existing

    partner = db.query(PharmacyPartner).filter(
        PharmacyPartner.pharmacy_id == order.pharmacy_id,
        PharmacyPartner.is_active == True,
    ).first()

    if not partner:
        logger.info("No active partner for pharmacy %s, skipping commission", order.pharmacy_id)
        return None

    amount = order.total * partner.commission_rate

    commission = Commission(
        order_id=order.id,
        pharmacy_partner_id=partner.id,
        order_total=order.total,
        commission_rate=partner.commission_rate,
        commission_amount=round(amount, 2),
        status=CommissionStatus.pending,
    )
    db.add(commission)
    db.commit()
    db.refresh(commission)

    logger.info(
        "Commission recorded: order=%s amount=%.2f rate=%.2f",
        order.id, amount, partner.commission_rate,
    )
    return commission
