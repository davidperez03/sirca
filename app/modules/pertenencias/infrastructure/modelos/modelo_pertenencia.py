from sqlalchemy import Column, String, DateTime, Enum, ForeignKey

# Dependencia interna para el modelo
from app.core.dependencias.dependencias import Base

class PertenenciaORM(Base):
    __tablename__ = "pertenencias"

    serial          = Column(String, primary_key=True, index=True)
    nombre          = Column(String, nullable=False)
    tipo            = Column(String, nullable=False)
    descripcion     = Column(String, nullable=True)
    foto            = Column(String, nullable=True)
    estado          = Column(String, nullable=False)
    usuario_id      = Column(String, ForeignKey("usuarios.numero_documento"), nullable=False)
    fecha_registro  = Column(DateTime, nullable=False)