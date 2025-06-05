from typing import Optional
from app.modules.pertenencias.domain.entidades.pertenencia import Pertenencia
from app.modules.pertenencias.domain.puertos.repositorio_pertenencias import RepositorioPertenencias

class ObtenerPertenencia:
    def __init__(self, repositorio: RepositorioPertenencias):
        self.repositorio = repositorio

    def ejecutar(self, id_pertenencia: int) -> Optional[Pertenencia]:
        """Obtiene una pertenencia por su ID único."""
        return self.repositorio.obtener_por_id(id_pertenencia)
    
    def ejecutar_por_serial(self, serial: str) -> Optional[Pertenencia]:
        """Obtiene una pertenencia por su serial (para compatibilidad)."""
        return self.repositorio.obtener_por_serial(serial)