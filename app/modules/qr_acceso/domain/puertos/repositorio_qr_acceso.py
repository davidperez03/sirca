'''
Puerto del repositorio para QR de acceso
'''
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from app.modules.qr_acceso.domain.entidades.qr_acceso import QRAcceso
from app.modules.qr_acceso.domain.entidades.registro_acceso import RegistroAcceso

class RepositorioQRAcceso(ABC):
    
    # ========== OPERACIONES QR ==========
    @abstractmethod
    def guardar_qr(self, qr_acceso: QRAcceso) -> None:
        """Guarda un QR de acceso temporal"""
        pass
    
    @abstractmethod
    def obtener_qr_por_jwt(self, token_jwt: str) -> Optional[QRAcceso]:
        """Obtiene un QR por su token JWT"""
        pass
    
    @abstractmethod
    def obtener_qrs_activos_usuario(self, usuario_id: str) -> List[QRAcceso]:
        """Obtiene QRs activos (no usados y no expirados) de un usuario"""
        pass
    
    @abstractmethod
    def marcar_qr_usado(self, qr_id: int, vigilante_id: str, ubicacion: str) -> None:
        """Marca un QR como usado"""
        pass
    
    @abstractmethod
    def limpiar_qrs_expirados(self) -> int:
        """Elimina QRs expirados y retorna cantidad eliminada"""
        pass
    
    # ========== OPERACIONES REGISTRO ACCESO ==========
    @abstractmethod
    def guardar_registro(self, registro: RegistroAcceso) -> None:
        """Guarda un registro de acceso"""
        pass
    
    @abstractmethod
    def obtener_ultimo_registro_usuario(self, usuario_id: str) -> Optional[RegistroAcceso]:
        """Obtiene el último registro de acceso de un usuario"""
        pass
    
    @abstractmethod
    def listar_registros_por_fecha(
        self, 
        fecha_inicio: datetime, 
        fecha_fin: datetime,
        usuario_id: Optional[str] = None
    ) -> List[RegistroAcceso]:
        """Lista registros de acceso por rango de fechas"""
        pass
    
    @abstractmethod
    def contar_registros_hoy(self) -> dict:
        """Cuenta registros del día actual"""
        pass
    
    @abstractmethod
    def obtener_usuarios_dentro(self) -> List[dict]:
        """Obtiene usuarios que están actualmente dentro"""
        pass