from enum import Enum

class TipoMovimiento(str, Enum):
    INGRESO = "INGRESO"
    SALIDA = "SALIDA"