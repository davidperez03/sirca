from typing import Optional
from typing import List
from app.modules.vehiculos.domain.entidades.vehiculo import Vehiculo
from app.modules.vehiculos.domain.puertos.repositorio_vehiculos import RepositorioVehiculos
from app.modules.autenticacion.domain.entidades.usuario import Usuario

class ListarVehiculosUsuario:
    def __init__(self, repositorio: RepositorioVehiculos):
        self.repositorio = repositorio

    def ejecutar(self, usuario: Usuario) -> List[Vehiculo]:
        return self.repositorio.listar_por_usuario(usuario.numero_documento.valor)