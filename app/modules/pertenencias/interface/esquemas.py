from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.modules.pertenencias.domain.objetos_de_valor.tipo_pertenencia import TipoPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.estado_pertenencia import EstadoPertenencia

class PertenenciaCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=50, description="Nombre de la pertenencia")
    tipo: TipoPertenencia = Field(..., description="Tipo de pertenencia")
    descripcion: Optional[str] = Field("", max_length=200, description="Descripción de la pertenencia")
    serial: Optional[str] = Field("", max_length=30, description="Serial o código único")
    estado: Optional[EstadoPertenencia] = Field(EstadoPertenencia.ACTIVO, description="Estado de la pertenencia")

    @validator('serial')
    def validar_serial_segun_tipo(cls, v, values):
        tipo = values.get('tipo')
        if tipo and TipoPertenencia.requiere_serial_obligatorio(tipo):
            if not v or not v.strip():
                raise ValueError(f"El serial es obligatorio para pertenencias de tipo '{tipo.value}'")
        return v

    @validator('nombre')
    def validar_nombre(cls, v):
        if not v or not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()

class PertenenciaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=50)
    tipo: Optional[TipoPertenencia] = None
    descripcion: Optional[str] = Field(None, max_length=200)
    serial: Optional[str] = Field(None, max_length=30)
    estado: Optional[EstadoPertenencia] = None

class PertenenciaRead(BaseModel):
    id: int
    nombre: str
    tipo: str
    descripcion: str
    serial: str
    foto: str
    foto_url: str  # URL pública para mostrar en templates
    estado: str
    usuario_id: str
    usuario_nombre: str
    fecha_registro: datetime
    tiene_serial: bool  # Indica si tiene serial

    @classmethod
    def from_domain(cls, p):
        return cls(
            id=p.id,
            nombre=p.nombre.valor,
            tipo=p.tipo.value,
            descripcion=p.descripcion.valor,
            serial=p.serial.valor,
            foto=p.foto.valor,
            foto_url=p.foto.obtener_url_publica(),
            estado=p.estado.value,
            usuario_id=p.usuario.numero_documento.valor,
            usuario_nombre=f"{p.usuario.nombres.valor} {p.usuario.apellidos.valor}",
            fecha_registro=p.fecha_registro,
            tiene_serial=bool(p.serial.valor)
        )

class PertenenciaResumen(BaseModel):
    """Esquema para listados y resúmenes."""
    id: int
    nombre: str
    tipo: str
    serial: str
    estado: str
    foto_url: str
    fecha_registro: datetime

    @classmethod
    def from_domain(cls, p):
        return cls(
            id=p.id,
            nombre=p.nombre.valor,
            tipo=p.tipo.value,
            serial=p.serial.valor,
            estado=p.estado.value,
            foto_url=p.foto.obtener_url_publica(),
            fecha_registro=p.fecha_registro
        )

class EstadisticasPertenencias(BaseModel):
    """Esquema para estadísticas de pertenencias."""
    total: int
    activas: int
    inactivas: int
    por_tipo: dict

class ResultadoBusqueda(BaseModel):
    """Esquema para resultados de búsqueda."""
    pertenencias: List[PertenenciaResumen]
    total: int
    termino: str

class TipoPertenenciaInfo(BaseModel):
    """Información sobre un tipo de pertenencia."""
    valor: str
    nombre: str
    requiere_serial: bool

    @classmethod
    def from_enum(cls, tipo: TipoPertenencia):
        return cls(
            valor=tipo.value,
            nombre=tipo.value,
            requiere_serial=TipoPertenencia.requiere_serial_obligatorio(tipo)
        )