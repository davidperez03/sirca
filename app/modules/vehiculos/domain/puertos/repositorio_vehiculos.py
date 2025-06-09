from abc import ABC, abstractmethod
from typing import List, Optional
from app.modules.vehiculos.domain.entidades.vehiculo import Vehiculo

class RepositorioVehiculos(ABC):
    @abstractmethod
    def agregar(self, vehiculo: Vehiculo) -> None:
        """Agrega un nuevo vehículo."""
        pass

    @abstractmethod
    def obtener_por_placa(self, placa: str) -> Optional[Vehiculo]:
        """Obtiene un vehículo por su placa (primary key)."""
        pass

    @abstractmethod
    def listar_por_usuario(self, usuario_id: str, incluir_inactivos: bool = False) -> List[Vehiculo]:
        """Lista todos los vehículos de un usuario."""
        pass

    @abstractmethod
    def listar_por_tipo(self, tipo: str, incluir_inactivos: bool = False) -> List[Vehiculo]:
        """Lista vehículos por tipo."""
        pass

    @abstractmethod
    def buscar_por_marca_modelo(self, termino: str, usuario_id: Optional[str] = None, incluir_inactivos: bool = False) -> List[Vehiculo]:
        """Busca vehículos por marca o modelo."""
        pass

    @abstractmethod
    def contar_por_usuario(self, usuario_id: str) -> dict:
        """Retorna estadísticas de vehículos por usuario."""
        pass

    @abstractmethod
    def actualizar(self, vehiculo: Vehiculo) -> None:
        """Actualiza un vehículo existente."""
        pass

    @abstractmethod
    def eliminar(self, placa: str) -> None:
        """Elimina un vehículo por su placa."""
        pass

    @abstractmethod
    def existe_placa(self, placa: str) -> bool:
        """Verifica si existe un vehículo con la placa dada."""
        pass