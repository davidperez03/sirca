from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class QRTemporal:
    """Entidad QR temporal para acceso único"""
    usuario_id: str
    codigo_qr: str
    fecha_generacion: datetime
    fecha_expiracion: datetime
    usado: bool = False
    fecha_uso: Optional[datetime] = None
    vigilante_uso: Optional[str] = None
    id: Optional[int] = None