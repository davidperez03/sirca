from typing import Optional
from app.modules.vehiculos.domain.entidades.vehiculo import Vehiculo
from app.modules.vehiculos.domain.puertos.repositorio_vehiculos import RepositorioVehiculos

class ObtenerVehiculo:
    def __init__(self, repositorio: RepositorioVehiculos):
        self.repositorio = repositorio

    def ejecutar(self, placa: str) -> Optional[Vehiculo]:
        """Obtiene un vehículo por su placa (primary key)."""
        return self.repositorio.obtener_por_placa(placa)