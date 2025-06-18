'''
Modelos ORM para el módulo de QR Acceso
'''
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey, Index
from app.core.dependencias.dependencias import Base

class QRAccesoORM(Base):
    __tablename__ = "qr_accesos"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(String, ForeignKey("usuarios.numero_documento"), nullable=False, index=True)
    token_jwt = Column(Text, nullable=False, unique=True, index=True)
    fecha_generacion = Column(DateTime, nullable=False, index=True)
    fecha_expiracion = Column(DateTime, nullable=False, index=True)
    duracion_minutos = Column(Integer, nullable=False)
    pertenencias_incluidas = Column(JSON, nullable=True)  # Lista de pertenencias
    vehiculos_incluidos = Column(JSON, nullable=True)     # Lista de vehículos
    usado = Column(Boolean, default=False, nullable=False, index=True)
    fecha_uso = Column(DateTime, nullable=True)
    vigilante_uso = Column(String, nullable=True)
    ubicacion_uso = Column(String, nullable=True)
    
    __table_args__ = (
        Index('ix_qr_usuario_activo', 'usuario_id', 'usado'),
        Index('ix_qr_expiracion_usado', 'fecha_expiracion', 'usado'),
        Index('ix_qr_generacion', 'fecha_generacion'),
    )


class RegistroAccesoORM(Base):
    __tablename__ = "registros_acceso"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(String, ForeignKey("usuarios.numero_documento"), nullable=False, index=True)
    tipo_movimiento = Column(String(10), nullable=False, index=True)  # INGRESO/SALIDA
    fecha_hora = Column(DateTime, nullable=False, index=True)
    vigilante_id = Column(String, nullable=False, index=True)
    ubicacion = Column(String(100), nullable=False, default="Entrada Principal")
    pertenencias_declaradas = Column(JSON, nullable=True)  # Lista de pertenencias
    vehiculos_declarados = Column(JSON, nullable=True)     # Lista de vehículos
    observaciones = Column(Text, nullable=True)
    qr_usado_id = Column(Integer, ForeignKey("qr_accesos.id"), nullable=True, index=True)
    
    __table_args__ = (
        Index('ix_registro_usuario_fecha', 'usuario_id', 'fecha_hora'),
        Index('ix_registro_tipo_fecha', 'tipo_movimiento', 'fecha_hora'),
        Index('ix_registro_vigilante_fecha', 'vigilante_id', 'fecha_hora'),
        Index('ix_registro_fecha_tipo', 'fecha_hora', 'tipo_movimiento'),
    )