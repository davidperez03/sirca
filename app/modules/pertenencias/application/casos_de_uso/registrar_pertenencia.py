from datetime import datetime
from app.modules.pertenencias.domain.entidades.pertenencia import Pertenencia
from app.modules.pertenencias.domain.objetos_de_valor.nombre_pertenencia import NombrePertenencia
from app.modules.pertenencias.domain.objetos_de_valor.tipo_pertenencia import TipoPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.descripcion_pertenencia import DescripcionPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.serial_pertenencia import SerialPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.foto_pertenencia import FotoPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.estado_pertenencia import EstadoPertenencia
from app.modules.pertenencias.domain.puertos.repositorio_pertenencias import RepositorioPertenencias
from app.modules.autenticacion.domain.entidades.usuario import Usuario

class RegistrarPertenencia:
    def __init__(self, repositorio: RepositorioPertenencias):
        self.repositorio = repositorio

    def ejecutar(
        self,
        nombre: str,
        tipo: str,
        descripcion: str,
        serial: str,
        foto: str,
        usuario: Usuario,
        estado: str = "Activo"
    ) -> Pertenencia:
        pertenencia = Pertenencia(
            nombre=NombrePertenencia(nombre),
            tipo=TipoPertenencia(tipo),
            descripcion=DescripcionPertenencia(descripcion),
            serial=SerialPertenencia(serial),
            foto=FotoPertenencia(foto),
            estado=EstadoPertenencia(estado),
            usuario=usuario,
            fecha_registro=datetime.utcnow()
        )
        self.repositorio.agregar(pertenencia)
        return pertenencia