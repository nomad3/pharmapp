from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin


class BmsDistribution(TimestampMixin, Base):
    __tablename__ = "bms_distributions"

    # Product identification
    active_ingredient = Column(String, nullable=True)
    composition = Column(String, nullable=True)
    measure = Column(String, nullable=True)
    product_commercial_name = Column(String, nullable=True)
    product_generic_name = Column(String, nullable=True)

    # Medication FK
    medication_id = Column(
        UUID(as_uuid=True),
        ForeignKey("medications.id"),
        nullable=True,
        index=True,
    )

    # Institution / destination
    institution_rut = Column(String, index=True, nullable=True)
    client_destination_name = Column(String, nullable=True)
    region = Column(String, nullable=True)
    comuna = Column(String, nullable=True)
    servicio_salud = Column(String, nullable=True)

    # Order details
    delivery_date = Column(Date, index=True, nullable=True)
    purchase_order = Column(String, nullable=True)
    sale_document = Column(String, nullable=True)

    # Quantities
    order_quantity = Column(Integer, nullable=True)
    unit_quantity = Column(Integer, nullable=True)
    units_per_package = Column(Integer, nullable=True)

    # Amounts
    gross_amount = Column(Float, nullable=True)
    net_amount = Column(Float, nullable=True)
    gross_unit_price = Column(Float, nullable=True)
    net_unit_price = Column(Float, nullable=True)

    # Classification
    market = Column(String, index=True, nullable=True)
    bms_competition = Column(String, index=True, nullable=True)
    provider_name = Column(String, nullable=True)
    distribution_channel = Column(String, nullable=True)
