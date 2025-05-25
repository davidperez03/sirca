'''
    Enum para los tipos de documentos de identificación en Colombia.
    Cada tipo de documento tiene un nombre descriptivo asociado.
'''

# Biblioteca estándar
from enum import Enum

class TipoDocumento(Enum):

    CC = "Cédula de Ciudadanía" 
    TI = "Tarjeta de Identidad"
    CE = "Cédula de Extranjería"
    PPT = "Permito de Protección Temporal"
    PAS = "Pasaporte"