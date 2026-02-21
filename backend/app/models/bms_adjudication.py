from sqlalchemy import Column, Date, Float, Integer, String

from app.models.base import Base, TimestampMixin


class BmsAdjudication(TimestampMixin, Base):
    __tablename__ = "bms_adjudications"

    # Adjudication metadata
    adquisicion = Column(String, nullable=True)
    rut_cliente = Column(String, index=True, nullable=True)
    fecha_adjudicacion = Column(Date, index=True, nullable=True)
    estado = Column(String, nullable=True)

    # Product identification
    pactivo = Column(String, nullable=True)
    composicion = Column(String, nullable=True)
    presentacion = Column(String, nullable=True)

    # Pricing and quantities
    precio_unit = Column(Float, nullable=True)
    cant_adjudicada = Column(Integer, nullable=True)
    valor_adjudicado = Column(Float, nullable=True)

    # Institution / provider
    razon_social_cliente = Column(String, nullable=True)
    corp_proveedor = Column(String, nullable=True)

    # Classification
    market = Column(String, index=True, nullable=True)
    bms_competition = Column(String, index=True, nullable=True)
