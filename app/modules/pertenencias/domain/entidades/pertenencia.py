'''
    Entidad de dominio para una Pertenencia de Usuario.
'''
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.modules.autenticacion.domain.entidades.usuario import Usuario
from app.modules.pertenencias.domain.objetos_de_valor.nombre_pertenencia import NombrePertenencia
from app.modules.pertenencias.domain.objetos_de_valor.tipo_pertenencia import TipoPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.descripcion_pertenencia import DescripcionPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.serial_pertenencia import SerialPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.foto_pertenencia import FotoPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.estado_pertenencia import EstadoPertenencia

@dataclass
class Pertenencia:
    nombre: NombrePertenencia
    tipo: TipoPertenencia
    descripcion: DescripcionPertenencia
    serial: SerialPertenencia
    foto: FotoPertenencia
    estado: EstadoPertenencia
    usuario: Usuario
    fecha_registro: datetime
    id: Optional[int] = None  