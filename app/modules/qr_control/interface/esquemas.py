from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class QRTemporalCreate(BaseModel):
    duracion_minutos: int = Field(5, ge=1, le=60, description="Duración del QR en minutos")

class QRTemporalRead(BaseModel):
    id: Optional[int]
    usuario_id: str
    codigo_qr: str
    fecha_generacion: datetime
    fecha_expiracion: datetime
    usado: bool
    fecha_uso: Optional[datetime]
    vigilante_uso: Optional[str]
    tiempo_restante_segundos: int

    @classmethod
    def from_domain(cls, qr):
        tiempo_restante = max(0, int((qr.fecha_expiracion - datetime.now()).total_seconds()))
        return cls(
            id=qr.id,
            usuario_id=qr.usuario_id,
            codigo_qr=qr.codigo_qr,
            fecha_generacion=qr.fecha_generacion,
            fecha_expiracion=qr.fecha_expiracion,
            usado=qr.usado,
            fecha_uso=qr.fecha_uso,
            vigilante_uso=qr.vigilante_uso,
            tiempo_restante_segundos=tiempo_restante
        )

class QRTemporalResponse(BaseModel):
    qr_data: QRTemporalRead
    qr_image: str  # Base64 encoded image
    success: bool = True
    message: str = "QR generado exitosamente"

class AccesoCreate(BaseModel):
    codigo_qr: str = Field(..., description="Código QR escaneado")
    vigilante_id: str = Field(..., description="ID del vigilante que procesa")
    ubicacion: str = Field("Entrada Principal", description="Ubicación del acceso")
    items_declarados: List[str] = Field(default_factory=list, description="IDs de items declarados")
    observaciones: str = Field("", max_length=500, description="Observaciones del acceso")

class AccesoRead(BaseModel):
    id: Optional[int]
    usuario_id: str
    usuario_nombre: str
    usuario_rol: str
    tipo_movimiento: str  # INGRESO o SALIDA
    fecha_hora: datetime
    vigilante_id: str
    ubicacion: str
    items_declarados: List[str]
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
            items_declarados=registro.items_declarados,
            observaciones=registro.observaciones
        )

class ValidacionQRResponse(BaseModel):
    valido: bool
    usuario_id: Optional[str] = None
    nombre_completo: Optional[str] = None
    rol: Optional[str] = None
    estado_actual: Optional[str] = None
    tipo_siguiente: Optional[str] = None  # INGRESO o SALIDA
    expira_en: Optional[int] = None  # segundos
    mensaje: str

class ReporteDiario(BaseModel):
    fecha: str
    total_accesos: int
    ingresos: int
    salidas: int
    usuarios_unicos: int
    dentro_actualmente: int
    accesos_por_hora: dict
    accesos_detalle: List[AccesoRead]

class EstadisticasGenerales(BaseModel):
    accesos_hoy: int
    accesos_mes: int
    ingresos_hoy: int
    salidas_hoy: int
    qr_expirados_limpiados: int

class FiltrosAcceso(BaseModel):
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    usuario_id: Optional[str] = None
    tipo_movimiento: Optional[str] = None  # INGRESO, SALIDA
    vigilante_id: Optional[str] = None
    ubicacion: Optional[str] = None

class AccesoReciente(BaseModel):
    """Para mostrar en tiempo real"""
    usuario_nombre: str
    usuario_id: str
    tipo_movimiento: str
    fecha_hora: datetime
    vigilante: str
    items_count: int
    hace_minutos: int

class EstadoUsuario(BaseModel):
    usuario_id: str
    estado: str  # DENTRO, FUERA, BLOQUEADO
    ultimo_acceso: Optional[AccesoRead] = None
    tiempo_dentro: Optional[int] = None  # minutos si está dentro

class DashboardData(BaseModel):
    """Datos para el dashboard en tiempo real"""
    estadisticas: EstadisticasGenerales
    accesos_recientes: List[AccesoReciente]
    personas_dentro: int
    alertas: List[str] = Field(default_factory=list)

class ProcesarAccesoResponse(BaseModel):
    """Respuesta después de procesar un acceso"""
    success: bool
    registro: AccesoRead
    mensaje: str
    nuevo_estado: str  # Estado del usuario después del acceso

    @classmethod
    def success_response(cls, registro, nuevo_estado: str):
        tipo = registro.tipo_movimiento.lower()
        return cls(
            success=True,
            registro=AccesoRead.from_domain(registro),
            mensaje=f"✅ {tipo.capitalize()} registrado correctamente",
            nuevo_estado=nuevo_estado
        )

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    codigo: Optional[str] = None

    @classmethod
    def from_exception(cls, e: Exception, codigo: str = None):
        return cls(
            error=str(e),
            codigo=codigo or "ERROR_GENERAL"
        )