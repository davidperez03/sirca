from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.modules.autenticacion.domain.entidades.usuario import Usuario
from app.modules.vehiculos.domain.objetos_de_valor.placa_vehiculo import PlacaVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.tipo_vehiculo import TipoVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.marca_vehiculo import MarcaVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.modelo_vehiculo import ModeloVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.color_vehiculo import ColorVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.foto_vehiculo import FotoVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.estado_vehiculo import EstadoVehiculo

@dataclass
class Vehiculo:
    placa: PlacaVehiculo  # Primary Key
    tipo: TipoVehiculo
    marca: MarcaVehiculo
    modelo: ModeloVehiculo
    color: ColorVehiculo
    foto: FotoVehiculo
    estado: EstadoVehiculo
    usuario: Usuario
    fecha_registro: datetime