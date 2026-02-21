from sqlalchemy import Column, String, Float, Integer, Date, DateTime
from app.models.base import Base, TimestampMixin


class CenabastInvoice(TimestampMixin, Base):
    __tablename__ = "cenabast_invoices"

    # Date
    fecha_doc = Column(Date, index=True, nullable=True)
    ano = Column(Integer, index=True, nullable=True)
    mes = Column(Integer, nullable=True)
    # Invoice
    n_factura_sap = Column(String, nullable=True)
    pos = Column(Integer, nullable=True)
    # Quantities
    cantidad_facturada = Column(Integer, nullable=True)
    cantidad_facturada_corregida = Column(Integer, nullable=True)
    cantidad_unitaria = Column(Integer, nullable=True)
    cantidad_unitaria_corregida = Column(Integer, nullable=True)
    # Client/Requesting
    rut_cliente_solicitante = Column(String, index=True, nullable=True)
    nombre_cliente_solicitante = Column(String, nullable=True)
    direccion_solicitante = Column(String, nullable=True)
    comuna_solicitante = Column(String, index=True, nullable=True)
    region_solicitante = Column(String, index=True, nullable=True)
    # Destination
    rut_pagador = Column(String, nullable=True)
    cliente_destinatario = Column(String, nullable=True)
    nombre_destinatario = Column(String, nullable=True)
    direccion_dest = Column(String, nullable=True)
    comuna_cliente_dest = Column(String, nullable=True)
    region_cliente_dest = Column(String, nullable=True)
    # Pricing
    valor_neto = Column(Float, nullable=True)
    impuesto = Column(Float, nullable=True)
    monto_bruto = Column(Float, nullable=True)
    # Product
    codigo_producto_comercial = Column(String, index=True, nullable=True)
    nombre_producto_comercial = Column(String, nullable=True)
    por = Column(String, nullable=True)
    grupo_articulo = Column(String, nullable=True)
    zgen = Column(String, nullable=True)
    nombre_material_generico = Column(String, index=True, nullable=True)
    # Sector
    sector = Column(String, nullable=True)
    nombre_sector = Column(String, nullable=True)
    # Cost/Margins
    costo_producto = Column(Float, nullable=True)
    margen_cenab = Column(Float, nullable=True)
    margen_op_log = Column(Float, nullable=True)
    # Other
    canal_distrib = Column(String, nullable=True)
    division = Column(String, nullable=True)
