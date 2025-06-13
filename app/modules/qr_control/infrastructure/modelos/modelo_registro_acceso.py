from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index, Integer, JSON
from app.core.dependencias.dependencias import Base

class RegistroAccesoORM(Base):
    __tablename__ = "registros_acceso"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(String, ForeignKey("usuarios.numero_documento"), nullable=False, index=True)
    tipo_movimiento = Column(String(10), nullable=False, index=True)  # INGRESO/SALIDA
    fecha_hora = Column(DateTime, nullable=False, index=True)
    vigilante_id = Column(String, nullable=False, index=True)
    ubicacion = Column(String(100), nullable=False, default="Entrada Principal")
    items_declarados = Column(JSON, nullable=True)  # Lista de IDs de items
    observaciones = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('ix_acceso_usuario_fecha', 'usuario_id', 'fecha_hora'),
        Index('ix_acceso_tipo_fecha', 'tipo_movimiento', 'fecha_hora'),
        Index('ix_acceso_vigilante_fecha', 'vigilante_id', 'fecha_hora'),
    )
