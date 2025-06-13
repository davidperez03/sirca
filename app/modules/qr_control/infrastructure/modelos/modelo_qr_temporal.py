from sqlalchemy import Column, String, DateTime, Boolean, Index, Integer, ForeignKey
from app.core.dependencias.dependencias import Base

class QRTemporalORM(Base):
    __tablename__ = "qr_temporales"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(String, ForeignKey("usuarios.numero_documento"), nullable=False, index=True)
    codigo_qr = Column(String(50), unique=True, nullable=False, index=True)
    fecha_generacion = Column(DateTime, nullable=False, index=True)
    fecha_expiracion = Column(DateTime, nullable=False, index=True)
    usado = Column(Boolean, default=False, nullable=False, index=True)
    fecha_uso = Column(DateTime, nullable=True)
    vigilante_uso = Column(String, nullable=True)
    
    __table_args__ = (
        Index('ix_qr_codigo_activo', 'codigo_qr', 'usado'),
        Index('ix_qr_usuario_activo', 'usuario_id', 'usado'),
        Index('ix_qr_expiracion', 'fecha_expiracion'),
    )