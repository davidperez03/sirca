from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from app.modules.qr_control.domain.entidades.registro_acceso import RegistroAcceso
from app.modules.qr_control.domain.entidades.qr_temporal import QRTemporal

class RepositorioAccesos(ABC):
    @abstractmethod
    def guardar_registro(self, registro: RegistroAcceso) -> None:
        pass
    
    @abstractmethod
    def obtener_ultimo_acceso(self, usuario_id: str) -> Optional[RegistroAcceso]:
        pass
    
    @abstractmethod
    def listar_accesos_por_fecha(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[RegistroAcceso]:
        pass
    
    @abstractmethod
    def guardar_qr_temporal(self, qr: QRTemporal) -> None:
        pass
    
    @abstractmethod
    def obtener_qr_temporal(self, codigo: str) -> Optional[QRTemporal]:
        pass
    
    @abstractmethod
    def marcar_qr_usado(self, codigo: str, vigilante_id: str) -> None:
        pass
    
    @abstractmethod
    def limpiar_qr_expirados(self) -> int:
        pass
    
    @abstractmethod
    def obtener_estado_usuario(self, usuario_id: str) -> str:
        pass