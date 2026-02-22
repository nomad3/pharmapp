import logging
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.gpo_group import GpoGroup
from app.models.gpo_member import GpoMember
from app.models.gpo_purchase_intent import GpoPurchaseIntent, IntentStatus
from app.models.gpo_group_order import GpoGroupOrder, GroupOrderStatus
from app.models.gpo_allocation import GpoAllocation
from app.models.gpo_facilitation_fee import GpoFacilitationFee
from app.models.cenabast_product import CenabastProduct

logger = logging.getLogger(__name__)


def get_aggregated_demand(db: Session, gpo_group_id: str, target_month: str):
    members = db.query(GpoMember.id).filter(
        GpoMember.gpo_group_id == gpo_group_id
    ).all()
    member_ids = [m.id for m in members]
    if not member_ids:
        return []

    group = db.query(GpoGroup).filter(GpoGroup.id == gpo_group_id).first()
    threshold = group.min_aggregation_threshold if group else 100

    rows = db.query(
        GpoPurchaseIntent.product_name,
        GpoPurchaseIntent.cenabast_product_id,
        func.sum(GpoPurchaseIntent.quantity_units).label("total_quantity"),
        func.count(func.distinct(GpoPurchaseIntent.gpo_member_id)).label("member_count"),
    ).filter(
        GpoPurchaseIntent.gpo_member_id.in_(member_ids),
        GpoPurchaseIntent.target_month == target_month,
        GpoPurchaseIntent.status == IntentStatus.submitted,
    ).group_by(
        GpoPurchaseIntent.product_name,
        GpoPurchaseIntent.cenabast_product_id,
    ).all()

    results = []
    for row in rows:
        total = int(row.total_quantity or 0)
        results.append({
            "product_name": row.product_name,
            "cenabast_product_id": str(row.cenabast_product_id) if row.cenabast_product_id else None,
            "total_quantity": total,
            "member_count": int(row.member_count or 0),
            "threshold": threshold,
            "threshold_met": total >= threshold,
        })
    results.sort(key=lambda x: x["total_quantity"], reverse=True)
    return results


def create_group_order_from_demand(
    db: Session,
    gpo_group_id: str,
    product_name: str,
    cenabast_product_id: str = None,
    target_month: str = "",
):
    group = db.query(GpoGroup).filter(GpoGroup.id == gpo_group_id).first()
    if not group:
        return None

    demand = get_aggregated_demand(db, gpo_group_id, target_month)
    product_demand = next(
        (d for d in demand if d["product_name"] == product_name),
        None,
    )
    if not product_demand:
        return None

    # Get PMVP for the product
    unit_price_pmvp = None
    if cenabast_product_id:
        cp = db.query(CenabastProduct).filter(CenabastProduct.id == cenabast_product_id).first()
        if cp:
            unit_price_pmvp = cp.precio_maximo_publico

    # Group price = PMVP (if available), no markup
    unit_price_group = unit_price_pmvp

    order = GpoGroupOrder(
        gpo_group_id=gpo_group_id,
        cenabast_product_id=cenabast_product_id,
        product_name=product_name,
        target_month=target_month,
        status=GroupOrderStatus.aggregated,
        total_quantity=product_demand["total_quantity"],
        member_count=product_demand["member_count"],
        unit_price_pmvp=unit_price_pmvp,
        unit_price_group=unit_price_group,
    )
    db.add(order)
    db.flush()

    # Link intents to order
    member_ids = [m.id for m in db.query(GpoMember.id).filter(GpoMember.gpo_group_id == gpo_group_id).all()]
    intents = db.query(GpoPurchaseIntent).filter(
        GpoPurchaseIntent.gpo_member_id.in_(member_ids),
        GpoPurchaseIntent.product_name == product_name,
        GpoPurchaseIntent.target_month == target_month,
        GpoPurchaseIntent.status == IntentStatus.submitted,
    ).all()

    for intent in intents:
        intent.status = IntentStatus.aggregated
        intent.group_order_id = order.id

    # Create allocations
    calculate_allocations(db, order, intents, group.facilitation_fee_rate)

    # Create facilitation fee record
    order_total = (unit_price_group or 0) * product_demand["total_quantity"]
    fee_amount = order_total * group.facilitation_fee_rate
    order.facilitation_fee = fee_amount

    fee = GpoFacilitationFee(
        group_order_id=order.id,
        order_total=order_total,
        fee_rate=group.facilitation_fee_rate,
        fee_amount=fee_amount,
    )
    db.add(fee)

    db.commit()
    db.refresh(order)
    return order


def calculate_allocations(db: Session, order, intents, fee_rate):
    unit_price = order.unit_price_group or 0

    for intent in intents:
        subtotal = unit_price * intent.quantity_units
        fee = subtotal * fee_rate

        allocation = GpoAllocation(
            group_order_id=order.id,
            gpo_member_id=intent.gpo_member_id,
            quantity_allocated=intent.quantity_units,
            unit_price=unit_price,
            subtotal=subtotal,
            facilitation_fee=fee,
        )
        db.add(allocation)


def update_group_order_status(db: Session, group_order_id: str, new_status: str):
    order = db.query(GpoGroupOrder).filter(GpoGroupOrder.id == group_order_id).first()
    if not order:
        return None

    order.status = new_status
    db.commit()
    db.refresh(order)
    return order


def get_member_savings(db: Session, gpo_member_id: str):
    allocations = db.query(GpoAllocation).filter(
        GpoAllocation.gpo_member_id == gpo_member_id,
    ).all()

    total_pmvp = 0
    total_group = 0
    order_count = 0

    for alloc in allocations:
        order = db.query(GpoGroupOrder).filter(GpoGroupOrder.id == alloc.group_order_id).first()
        if order and order.unit_price_pmvp and order.unit_price_group:
            total_pmvp += order.unit_price_pmvp * alloc.quantity_allocated
            total_group += alloc.subtotal
            order_count += 1

    savings = total_pmvp - total_group
    savings_pct = round(savings / total_pmvp * 100, 1) if total_pmvp > 0 else 0

    return {
        "total_orders": order_count,
        "total_pmvp_cost": round(total_pmvp, 0),
        "total_group_cost": round(total_group, 0),
        "total_savings": round(savings, 0),
        "savings_pct": savings_pct,
    }


def get_group_savings(db: Session, gpo_group_id: str):
    members = db.query(GpoMember).filter(GpoMember.gpo_group_id == gpo_group_id).all()
    summaries = []
    for member in members:
        savings = get_member_savings(db, str(member.id))
        if savings["total_orders"] > 0:
            summaries.append({
                "member_id": str(member.id),
                "institution_name": member.institution_name,
                "total_savings": savings["total_savings"],
                "order_count": savings["total_orders"],
            })
    return summaries
