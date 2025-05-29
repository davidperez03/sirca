'''
    Enum para los tipos de pertenencia permitidos.
'''
from enum import Enum

class TipoPertenencia(str, Enum):
    ELECTRONICO = "Electrónico"
    HERRAMIENTA = "Herramienta"
    ACCESORIO = "Accesorio"
    OTRO = "Otro"