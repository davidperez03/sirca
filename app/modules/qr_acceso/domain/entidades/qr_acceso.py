'''
Entidad QR de Acceso - Representa un código QR temporal con JWT para acceso
'''
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
from app.modules.autenticacion.domain.entidades.usuario import Usuario

@dataclass
class QRAcceso:
    """Entidad que representa un QR de acceso temporal con JWT"""
    usuario: Usuario
    token_jwt: str  # JWT que contiene toda la información
    fecha_generacion: datetime
    fecha_expiracion: datetime
    duracion_minutos: int
    pertenencias_incluidas: List[Dict]  # [{"id": 1, "nombre": "Laptop"}]
    vehiculos_incluidos: List[Dict]     # [{"placa": "ABC123", "tipo": "Automóvil"}]
    usado: bool = False
    fecha_uso: Optional[datetime] = None
    vigilante_uso: Optional[str] = None
    ubicacion_uso: Optional[str] = None
    id: Optional[int] = None
    
    @property
    def esta_expirado(self) -> bool:
        """Verifica si el QR ha expirado"""
        return datetime.now() > self.fecha_expiracion
    
    @property
    def puede_usarse(self) -> bool:
        """Verifica si el QR puede ser usado"""
        return not self.usado and not self.esta_expirado
    
    @property
    def segundos_restantes(self) -> int:
        """Retorna segundos restantes antes de expirar"""
        if self.esta_expirado:
            return 0
        return int((self.fecha_expiracion - datetime.now()).total_seconds())
    
    @property
    def tiene_items_declarados(self) -> bool:
        """Verifica si tiene pertenencias o vehículos incluidos"""
        return len(self.pertenencias_incluidas) > 0 or len(self.vehiculos_incluidos) > 0
    
    def marcar_como_usado(self, vigilante_id: str, ubicacion: str = "Entrada Principal"):
        """Marca el QR como usado"""
        if not self.puede_usarse:
            raise ValueError("QR no puede ser usado (ya usado o expirado)")
        
        self.usado = True
        self.fecha_uso = datetime.now()
        self.vigilante_uso = vigilante_id
        self.ubicacion_uso = ubicacion