'''
    Enum mejorado para los tipos de pertenencia permitidos.
    Incluye tipos que requieren serial obligatorio.
'''
from enum import Enum

class TipoPertenencia(str, Enum):
    ELECTRONICO = "Electrónico"
    MEDIOS_DE_TRANSPORTE = "Medios de Transporte"
    HERRAMIENTA = "Herramienta"
    ACCESORIO = "Accesorio"
    ROPA = "Ropa"
    EQUIPAMIENTO_DEPORTIVO = "Equipamiento Deportivo"
    MOBILIARIO = "Mobiliario"
    INSTRUMENTO_MUSICAL = "Instrumento Musical"
    OTRO = "Otro"

    @classmethod
    def requiere_serial_obligatorio(cls, tipo: 'TipoPertenencia') -> bool:
        """Retorna True si el tipo de pertenencia requiere serial obligatorio."""
        tipos_con_serial_obligatorio = {
            cls.ELECTRONICO,
            cls.MEDIOS_DE_TRANSPORTE
        }
        return tipo in tipos_con_serial_obligatorio