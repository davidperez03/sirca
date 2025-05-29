from typing import List
from app.modules.pertenencias.domain.entidades.pertenencia import Pertenencia
from app.modules.pertenencias.domain.puertos.repositorio_pertenencias import RepositorioPertenencias
from app.modules.autenticacion.domain.entidades.usuario import Usuario

class ListarPertenenciasUsuario:
    def __init__(self, repositorio: RepositorioPertenencias):
        self.repositorio = repositorio

    def ejecutar(self, usuario: Usuario) -> List[Pertenencia]:
        return self.repositorio.listar_por_usuario(usuario.numero_documento.valor)