'''
    Utilidades para el manejo de fechas y zonas horarias.
'''

from datetime import datetime
import pytz
from app.core.config import settings

def obtener_fecha_local() -> datetime:
    """
    Obtiene la fecha y hora actual en la zona horaria configurada.
    """
    zona_horaria = pytz.timezone(settings.timezone)
    return datetime.now(zona_horaria)

def convertir_a_local(fecha_utc: datetime) -> datetime:
    """
    Convierte una fecha UTC a la zona horaria local configurada.
    """
    if fecha_utc.tzinfo is None:
        fecha_utc = pytz.utc.localize(fecha_utc)
    
    zona_horaria = pytz.timezone(settings.timezone)
    return fecha_utc.astimezone(zona_horaria)

def formatear_fecha_local(fecha: datetime, formato: str = "%d/%m/%Y %H:%M") -> str:
    """
    Formatea una fecha en la zona horaria local.
    """
    fecha_local = convertir_a_local(fecha) if fecha.tzinfo else fecha
    return fecha_local.strftime(formato)