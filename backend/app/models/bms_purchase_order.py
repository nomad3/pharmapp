from sqlalchemy import Column, Date, Float, Integer, String

from app.models.base import Base, TimestampMixin


class BmsPurchaseOrder(TimestampMixin, Base):
    __tablename__ = "bms_purchase_orders"

    # Product identification
    pactivo = Column(String, nullable=True)
    presentacion = Column(String, nullable=True)
    medida = Column(String, nullable=True)

    # Quantities and pricing
    cant_pht = Column(Integer, nullable=True)
    precio_pht = Column(Float, nullable=True)
    valor_total = Column(Float, nullable=True)

    # Date
    fecha = Column(Date, index=True, nullable=True)

    # Institution / location
    institucion = Column(String, nullable=True)
    region = Column(String, nullable=True)
    comuna = Column(String, nullable=True)
    supplier = Column(String, nullable=True)
    corporation = Column(String, nullable=True)

    # Classification
    market = Column(String, index=True, nullable=True)
    bms_competition = Column(String, index=True, nullable=True)

    # Order metadata
    tipo_oc = Column(String, nullable=True)
    id_licitacion = Column(String, nullable=True)
