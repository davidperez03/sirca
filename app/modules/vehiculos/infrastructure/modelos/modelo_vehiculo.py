from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship

# Dependencia interna para el modelo
from app.core.dependencias.dependencias import Base

class VehiculoORM(Base):
    __tablename__ = "vehiculos"

    placa           = Column(String(6), primary_key=True, index=True)  # Primary Key
    tipo            = Column(String(20), nullable=False, index=True)
    marca           = Column(String(30), nullable=False, index=True)
    modelo          = Column(String(40), nullable=False, index=True)
    color           = Column(String(25), nullable=False, index=True)
    foto            = Column(String(255), nullable=True)
    estado          = Column(String(20), nullable=False, default="Activo", index=True)
    usuario_id      = Column(String, ForeignKey("usuarios.numero_documento"), nullable=False, index=True)
    fecha_registro  = Column(DateTime, nullable=False, index=True)

    # Índices compuestos para optimizar consultas
    __table_args__ = (
        Index('ix_vehiculos_usuario_estado', 'usuario_id', 'estado'),
        Index('ix_vehiculos_tipo_estado', 'tipo', 'estado'),
        Index('ix_vehiculos_fecha_usuario', 'fecha_registro', 'usuario_id'),
        Index('ix_vehiculos_marca_modelo', 'marca', 'modelo'),
    )