from typing import Optional
from app.modules.pertenencias.domain.entidades.pertenencia import Pertenencia
from app.modules.pertenencias.domain.puertos.repositorio_pertenencias import RepositorioPertenencias

class ObtenerPertenencia:
    def __init__(self, repositorio: RepositorioPertenencias):
        self.repositorio = repositorio

    def ejecutar(self, serial: str) -> Optional[Pertenencia]:
        return self.repositorio.obtener_por_serial(serial)