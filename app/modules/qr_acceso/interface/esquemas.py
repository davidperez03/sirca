'''
Esquemas Pydantic para QR Acceso
'''
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime

class QRGenerarRequest(BaseModel):
    duracion_minutos: int = Field(15, ge=1, le=60, description="Duración del QR en minutos")
    incluir_pertenencias: bool = Field(True, description="Incluir pertenencias activas")
    incluir_vehiculos: bool = Field(True, description="Incluir vehículos activos")

class QRGenerarResponse(BaseModel):
    success: bool = True
    qr_id: int
    token_jwt: str
    imagen_base64: str
    fecha_expiracion: datetime
    duracion_minutos: int
    pertenencias_incluidas: List[Dict]
    vehiculos_incluidos: List[Dict]
    segundos_restantes: int
    mensaje: str = "QR generado exitosamente"

class QRValidarRequest(BaseModel):
    token_jwt: str = Field(..., description="Token JWT del QR")

class QRValidarResponse(BaseModel):
    valido: bool
    usuario_id: Optional[str] = None
    nombre_completo: Optional[str] = None
    rol: Optional[str] = None
    estado_actual: Optional[str] = None
    siguiente_movimiento: Optional[str] = None
    pertenencias_incluidas: List[Dict] = Field(default_factory=list)
    vehiculos_incluidos: List[Dict] = Field(default_factory=list)
    segundos_restantes: Optional[int] = None
    mensaje: str

class AccesoProcesarRequest(BaseModel):
    token_jwt: str = Field(..., description="Token JWT del QR")
    ubicacion: str = Field("Entrada Principal", description="Ubicación del acceso")
    observaciones: str = Field("", max_length=500, description="Observaciones adicionales")

class AccesoProcesarResponse(BaseModel):
    success: bool
    registro_id: int
    tipo_movimiento: str
    usuario_nombre: str
    fecha_hora: datetime
    pertenencias_procesadas: List[Dict]
    vehiculos_procesados: List[Dict]
    nuevo_estado: str
    mensaje: str

class RegistroAccesoRead(BaseModel):
    id: int
    usuario_id: str
    usuario_nombre: str
    usuario_rol: str
    tipo_movimiento: str
    fecha_hora: datetime
    vigilante_id: str
    ubicacion: str
    pertenencias_declaradas: List[Dict]
    vehiculos_declarados: List[Dict]
    total_items: int
    resumen_items: str
    observaciones: str

    @classmethod
    def from_domain(cls, registro):
        return cls(
            id=registro.id,
            usuario_id=registro.usuario.numero_documento.valor,
            usuario_nombre=f"{registro.usuario.nombres.valor} {registro.usuario.apellidos.valor}",
            usuario_rol=registro.usuario.rol.value,
            tipo_movimiento=registro.tipo_movimiento,
            fecha_hora=registro.fecha_hora,
            vigilante_id=registro.vigilante_id,
            ubicacion=registro.ubicacion,
            pertenencias_declaradas=registro.pertenencias_declaradas,
            vehiculos_declarados=registro.vehiculos_declarados,
            total_items=registro.total_items_declarados,
            resumen_items=registro.resumen_items,
            observaciones=registro.observaciones
        )

class EstadisticasAcceso(BaseModel):
    total_hoy: int
    ingresos_hoy: int
    salidas_hoy: int
    dentro_estimado: int
    usuarios_dentro: List[Dict]
    qrs_activos: int

class UsuarioDentroInfo(BaseModel):
    usuario_id: str
    nombre: str
    rol: str
    hora_ingreso: datetime
    tiempo_dentro_minutos: int
    tiempo_dentro_horas: float
    ubicacion_ingreso: str

    @validator('tiempo_dentro_horas', pre=True, always=True)
    def calcular_horas(cls, v, values):
        return round(values.get('tiempo_dentro_minutos', 0) / 60, 1)

class DashboardVigilanteData(BaseModel):
    estadisticas: EstadisticasAcceso
    registros_recientes: List[RegistroAccesoRead]
    alertas: List[str] = Field(default_factory=list)

class ErrorQRResponse(BaseModel):
    success: bool = False
    error: str
    codigo_error: str
    timestamp: datetime

    @classmethod
    def crear_error(cls, mensaje: str, codigo: str = "QR_ERROR"):
        return cls(
            error=mensaje,
            codigo_error=codigo,
            timestamp=datetime.now()
        )