from abc import ABC, abstractmethod
from typing import List, Optional
from app.modules.pertenencias.domain.entidades.pertenencia import Pertenencia

class RepositorioPertenencias(ABC):
    @abstractmethod
    def agregar(self, pertenencia: Pertenencia) -> None:
        pass

    @abstractmethod
    def obtener_por_serial(self, serial: str) -> Optional[Pertenencia]:
        pass

    @abstractmethod
    def listar_por_usuario(self, usuario_id: str) -> List[Pertenencia]:
        pass

    @abstractmethod
    def actualizar(self, pertenencia: Pertenencia) -> None:
        pass

    @abstractmethod
    def eliminar(self, serial: str) -> None:
        pass