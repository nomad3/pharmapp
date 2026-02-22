import logging
from datetime import datetime, timezone

import stripe
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.organization import Organization
from app.models.subscription import Subscription, SubscriptionTier, SubscriptionStatus

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_customer(org: Organization) -> str:
    customer = stripe.Customer.create(
        name=org.name,
        metadata={"org_id": str(org.id), "org_slug": org.slug},
    )
    return customer.id


def create_checkout_session(org: Organization, tier: str, return_url: str = None) -> str:
    price_id = (
        settings.STRIPE_PRICE_ID_PRO if tier == "pro"
        else settings.STRIPE_PRICE_ID_ENTERPRISE
    )
    if not price_id:
        raise ValueError(f"No Stripe price configured for tier: {tier}")

    if not org.stripe_customer_id:
        raise ValueError("Organization has no Stripe customer ID")

    base_url = return_url or "http://localhost:3000"
    session = stripe.checkout.Session.create(
        customer=org.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{base_url}/org/{org.slug}/billing?success=true",
        cancel_url=f"{base_url}/pricing?canceled=true",
        metadata={"org_id": str(org.id), "tier": tier},
    )
    return session.url


def create_portal_session(customer_id: str, return_url: str = None) -> str:
    base_url = return_url or "http://localhost:3000"
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{base_url}/org/settings",
    )
    return session.url


def handle_webhook(db: Session, payload: bytes, sig_header: str):
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.error("Stripe webhook error: %s", e)
        raise

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        _handle_checkout_completed(db, data)
    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        _handle_subscription_change(db, data)

    return {"status": "ok"}


def _handle_checkout_completed(db: Session, session_data: dict):
    org_id = session_data.get("metadata", {}).get("org_id")
    tier = session_data.get("metadata", {}).get("tier", "pro")
    stripe_sub_id = session_data.get("subscription")

    if not org_id:
        return

    sub = db.query(Subscription).filter(Subscription.org_id == org_id).first()
    if sub:
        sub.tier = SubscriptionTier(tier)
        sub.status = SubscriptionStatus.active
        sub.stripe_subscription_id = stripe_sub_id
    else:
        sub = Subscription(
            org_id=org_id,
            tier=SubscriptionTier(tier),
            status=SubscriptionStatus.active,
            stripe_subscription_id=stripe_sub_id,
        )
        db.add(sub)
    db.commit()


def _handle_subscription_change(db: Session, sub_data: dict):
    stripe_sub_id = sub_data.get("id")
    sub = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_sub_id
    ).first()
    if not sub:
        return

    status = sub_data.get("status", "")
    if status == "active":
        sub.status = SubscriptionStatus.active
    elif status in ("canceled", "unpaid"):
        sub.status = SubscriptionStatus.canceled
        sub.tier = SubscriptionTier.free
    elif status == "past_due":
        sub.status = SubscriptionStatus.past_due

    period_end = sub_data.get("current_period_end")
    if period_end:
        sub.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)
    period_start = sub_data.get("current_period_start")
    if period_start:
        sub.current_period_start = datetime.fromtimestamp(period_start, tz=timezone.utc)

    db.commit()
