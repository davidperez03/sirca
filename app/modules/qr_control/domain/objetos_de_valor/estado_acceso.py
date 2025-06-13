from enum import Enum

class EstadoAcceso(str, Enum):
    FUERA = "FUERA"
    DENTRO = "DENTRO"
    BLOQUEADO = "BLOQUEADO"