from app.modules.pertenencias.domain.puertos.repositorio_pertenencias import RepositorioPertenencias

class EliminarPertenencia:
    def __init__(self, repositorio: RepositorioPertenencias):
        self.repositorio = repositorio

    def ejecutar(self, serial: str) -> None:
        self.repositorio.eliminar(serial)