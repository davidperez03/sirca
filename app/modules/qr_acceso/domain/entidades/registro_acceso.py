'''
Entidad Registro de Acceso - Representa un movimiento de ingreso/salida
'''
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
from app.modules.autenticacion.domain.entidades.usuario import Usuario

@dataclass
class RegistroAcceso:
    """Entidad que representa un registro de acceso (ingreso/salida)"""
    usuario: Usuario
    tipo_movimiento: str  # "INGRESO" o "SALIDA"
    fecha_hora: datetime
    vigilante_id: str
    ubicacion: str
    pertenencias_declaradas: List[Dict]  # [{"id": 1, "nombre": "Laptop"}]
    vehiculos_declarados: List[Dict]     # [{"placa": "ABC123", "tipo": "Automóvil"}]
    observaciones: str
    qr_usado_id: Optional[int] = None  # ID del QR que se usó
    id: Optional[int] = None
    
    @property
    def total_items_declarados(self) -> int:
        """Total de items declarados (pertenencias + vehículos)"""
        return len(self.pertenencias_declaradas) + len(self.vehiculos_declarados)
    
    @property
    def resumen_items(self) -> str:
        """Resumen de items declarados para mostrar"""
        items = []
        if self.pertenencias_declaradas:
            items.append(f"{len(self.pertenencias_declaradas)} pertenencia(s)")
        if self.vehiculos_declarados:
            items.append(f"{len(self.vehiculos_declarados)} vehículo(s)")
        
        return ", ".join(items) if items else "Sin items"
    
    @property
    def es_ingreso(self) -> bool:
        """Verifica si es un movimiento de ingreso"""
        return self.tipo_movimiento == "INGRESO"
    
    @property
    def es_salida(self) -> bool:
        """Verifica si es un movimiento de salida"""
        return self.tipo_movimiento == "SALIDA"