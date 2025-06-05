from abc import ABC, abstractmethod
from typing import List, Optional
from app.modules.pertenencias.domain.entidades.pertenencia import Pertenencia

class RepositorioPertenencias(ABC):
    @abstractmethod
    def agregar(self, pertenencia: Pertenencia) -> None:
        """Agrega una nueva pertenencia."""
        pass

    @abstractmethod
    def obtener_por_id(self, id: int) -> Optional[Pertenencia]:
        """Obtiene una pertenencia por su ID único."""
        pass

    @abstractmethod
    def obtener_por_serial(self, serial: str) -> Optional[Pertenencia]:
        """Obtiene una pertenencia por su serial (si tiene)."""
        pass

    @abstractmethod
    def listar_por_usuario(self, usuario_id: str, incluir_inactivos: bool = False) -> List[Pertenencia]:
        """Lista todas las pertenencias de un usuario."""
        pass

    @abstractmethod
    def listar_por_tipo(self, tipo: str, incluir_inactivos: bool = False) -> List[Pertenencia]:
        """Lista pertenencias por tipo."""
        pass

    @abstractmethod
    def buscar_por_nombre(self, termino: str, usuario_id: Optional[str] = None, incluir_inactivos: bool = False) -> List[Pertenencia]:
        """Busca pertenencias por nombre."""
        pass

    @abstractmethod
    def contar_por_usuario(self, usuario_id: str) -> dict:
        """Retorna estadísticas de pertenencias por usuario."""
        pass

    @abstractmethod
    def actualizar(self, pertenencia: Pertenencia) -> None:
        """Actualiza una pertenencia existente."""
        pass

    @abstractmethod
    def eliminar(self, id: int) -> None:
        """Elimina una pertenencia por su ID."""
        pass