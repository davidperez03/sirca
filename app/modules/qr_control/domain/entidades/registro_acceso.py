from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from app.modules.autenticacion.domain.entidades.usuario import Usuario

@dataclass
class RegistroAcceso:
    """Entidad que representa un registro de acceso (ingreso/salida)"""
    usuario: Usuario
    tipo_movimiento: str  # "INGRESO" o "SALIDA"
    fecha_hora: datetime
    vigilante_id: str
    ubicacion: str
    items_declarados: List[str]  # IDs de pertenencias/vehículos
    observaciones: str
    id: Optional[int] = None
