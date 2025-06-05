from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index, Integer
from sqlalchemy.orm import relationship

# Dependencia interna para el modelo
from app.core.dependencias.dependencias import Base

class PertenenciaORM(Base):
    __tablename__ = "pertenencias"

    id              = Column(Integer, primary_key=True, index=True, autoincrement=True)
    serial          = Column(String(30), nullable=True, index=True)  # Ahora opcional
    nombre          = Column(String(50), nullable=False, index=True)
    tipo            = Column(String(50), nullable=False, index=True)
    descripcion     = Column(Text, nullable=True)
    foto            = Column(String(255), nullable=True)
    estado          = Column(String(20), nullable=False, default="Activo", index=True)
    usuario_id      = Column(String, ForeignKey("usuarios.numero_documento"), nullable=False, index=True)
    fecha_registro  = Column(DateTime, nullable=False, index=True)

    # Índices compuestos para optimizar consultas
    __table_args__ = (
        Index('ix_pertenencias_usuario_estado', 'usuario_id', 'estado'),
        Index('ix_pertenencias_tipo_estado', 'tipo', 'estado'),
        Index('ix_pertenencias_fecha_usuario', 'fecha_registro', 'usuario_id'),
        Index('ix_pertenencias_serial_unique', 'serial', unique=True),  # Serial único cuando existe
    )