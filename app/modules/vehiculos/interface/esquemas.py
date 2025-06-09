from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.modules.vehiculos.domain.objetos_de_valor.tipo_vehiculo import TipoVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.estado_vehiculo import EstadoVehiculo

class VehiculoCreate(BaseModel):
    placa: str = Field(..., min_length=5, max_length=6, description="Placa del vehículo")
    tipo: TipoVehiculo = Field(..., description="Tipo de vehículo")
    marca: str = Field(..., min_length=2, max_length=30, description="Marca del vehículo")
    modelo: str = Field(..., min_length=1, max_length=40, description="Modelo del vehículo")
    color: str = Field(..., min_length=3, max_length=25, description="Color del vehículo")
    estado: Optional[EstadoVehiculo] = Field(EstadoVehiculo.ACTIVO, description="Estado del vehículo")

    @validator('placa')
    def validar_placa_segun_tipo(cls, v, values):
        import re
        if not v or not v.strip():
            raise ValueError("La placa no puede estar vacía")
        
        placa_limpia = v.strip().upper()
        tipo = values.get('tipo')
        
        # Validar formato según tipo
        if tipo == TipoVehiculo.MOTOCICLETA:
            if not (re.match(r'^[A-Z]{3}[0-9]{2}$', placa_limpia) or 
                    re.match(r'^[A-Z]{3}[0-9]{2}[A-Z]$', placa_limpia)):
                raise ValueError("Formato de placa inválido para motocicleta. Use: ABC12 o ABC12D")
        elif tipo == TipoVehiculo.AUTOMOVIL:
            if not re.match(r'^[A-Z]{3}[0-9]{3}$', placa_limpia):
                raise ValueError("Formato de placa inválido para automóvil. Use: ABC123")
        
        return placa_limpia

    @validator('marca')
    def validar_marca(cls, v):
        if not v or not v.strip():
            raise ValueError("La marca no puede estar vacía")
        return v.strip()

    @validator('modelo')
    def validar_modelo(cls, v):
        if not v or not v.strip():
            raise ValueError("El modelo no puede estar vacío")
        return v.strip()

    @validator('color')
    def validar_color(cls, v):
        if not v or not v.strip():
            raise ValueError("El color no puede estar vacío")
        return v.strip()

class VehiculoUpdate(BaseModel):
    tipo: Optional[TipoVehiculo] = None
    marca: Optional[str] = Field(None, min_length=2, max_length=30)
    modelo: Optional[str] = Field(None, min_length=1, max_length=40)
    color: Optional[str] = Field(None, min_length=3, max_length=25)
    estado: Optional[EstadoVehiculo] = None

class VehiculoRead(BaseModel):
    placa: str
    tipo: str
    marca: str
    modelo: str
    color: str
    foto: str
    foto_url: str  # URL pública para mostrar en templates
    estado: str
    usuario_id: str
    usuario_nombre: str
    fecha_registro: datetime

    @classmethod
    def from_domain(cls, v):
        return cls(
            placa=v.placa.valor,
            tipo=v.tipo.value,
            marca=v.marca.valor,
            modelo=v.modelo.valor,
            color=v.color.valor,
            foto=v.foto.valor,
            foto_url=v.foto.obtener_url_publica(),
            estado=v.estado.value,
            usuario_id=v.usuario.numero_documento.valor,
            usuario_nombre=f"{v.usuario.nombres.valor} {v.usuario.apellidos.valor}",
            fecha_registro=v.fecha_registro
        )

class VehiculoResumen(BaseModel):
    """Esquema para listados y resúmenes."""
    placa: str
    tipo: str
    marca: str
    modelo: str
    color: str
    estado: str
    foto_url: str
    fecha_registro: datetime

    @classmethod
    def from_domain(cls, v):
        return cls(
            placa=v.placa.valor,
            tipo=v.tipo.value,
            marca=v.marca.valor,
            modelo=v.modelo.valor,
            color=v.color.valor,
            estado=v.estado.value,
            foto_url=v.foto.obtener_url_publica(),
            fecha_registro=v.fecha_registro
        )

class EstadisticasVehiculos(BaseModel):
    """Esquema para estadísticas de vehículos."""
    total: int
    activos: int
    inactivos: int
    por_tipo: dict

class ResultadoBusquedaVehiculos(BaseModel):
    """Esquema para resultados de búsqueda."""
    vehiculos: List[VehiculoResumen]
    total: int
    termino: str

class TipoVehiculoInfo(BaseModel):
    """Información sobre un tipo de vehículo."""
    valor: str
    nombre: str
    formato_placa: str
    descripcion: str

    @classmethod
    def from_enum(cls, tipo: TipoVehiculo):
        return cls(
            valor=tipo.value,
            nombre=tipo.value,
            formato_placa=TipoVehiculo.obtener_formato_placa(tipo),
            descripcion=TipoVehiculo.obtener_descripcion(tipo)
        )