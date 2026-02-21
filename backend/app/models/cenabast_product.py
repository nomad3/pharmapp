from sqlalchemy import Column, String, Float, Integer, Date, Boolean
from app.models.base import Base, TimestampMixin


class CenabastProduct(TimestampMixin, Base):
    __tablename__ = "cenabast_products"

    codigo_producto = Column(String, unique=True, index=True, nullable=False)
    nombre_producto = Column(String, nullable=True)
    nombre_proveedor = Column(String, nullable=True, index=True)
    precio_maximo_publico = Column(Float, nullable=True)
    # Extra fields from active PMVP list
    zgen = Column(String, nullable=True)
    nombre_generico = Column(String, nullable=True, index=True)
    fecha_cc = Column(Date, nullable=True)
    activo = Column(Boolean, nullable=True)
