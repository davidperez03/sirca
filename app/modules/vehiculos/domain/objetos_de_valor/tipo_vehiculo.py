"""
Enum para los tipos de vehículo permitidos: solo motocicletas y automóviles.
"""
from enum import Enum

class TipoVehiculo(str, Enum):
    MOTOCICLETA = "Motocicleta"
    AUTOMOVIL = "Automóvil"

    @classmethod
    def obtener_formato_placa(cls, tipo: 'TipoVehiculo') -> str:
        """Retorna el formato de placa esperado para el tipo de vehículo."""
        formatos = {
            cls.MOTOCICLETA: "ABC12 o ABC12D",
            cls.AUTOMOVIL: "ABC123"
        }
        return formatos.get(tipo, "Formato no definido")

    @classmethod
    def obtener_descripcion(cls, tipo: 'TipoVehiculo') -> str:
        """Retorna una descripción del tipo de vehículo."""
        descripciones = {
            cls.MOTOCICLETA: "Motocicleta - Placa de 5 o 6 caracteres",
            cls.AUTOMOVIL: "Automóvil - Placa de 6 caracteres"
        }
        return descripciones.get(tipo, "Tipo no definido")