'''
    Enum para el estado de la pertenencia: solo Activo o Inactivo.
'''
from enum import Enum

class EstadoPertenencia(str, Enum):
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"