"""
Enum para el estado del vehículo: solo Activo o Inactivo.
"""
from enum import Enum

class EstadoVehiculo(str, Enum):
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"