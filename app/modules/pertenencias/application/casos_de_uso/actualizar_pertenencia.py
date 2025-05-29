from app.modules.pertenencias.domain.entidades.pertenencia import Pertenencia
from app.modules.pertenencias.domain.puertos.repositorio_pertenencias import RepositorioPertenencias

class ActualizarPertenencia:
    def __init__(self, repositorio: RepositorioPertenencias):
        self.repositorio = repositorio

    def ejecutar(self, pertenencia: Pertenencia) -> None:
        self.repositorio.actualizar(pertenencia)