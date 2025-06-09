"""
Objeto de valor para el color del vehículo.
"""
import re
from dataclasses import dataclass

COLORES_PROHIBIDOS = {"test", "demo", "null", "undefined", "admin"}

@dataclass(frozen=True)
class ColorVehiculo:
    valor: str

    def __post_init__(self):
        limpio = self.valor.strip() if self.valor else ""
        
        if not limpio:
            raise ValueError("El color es obligatorio")
        
        if len(limpio) < 3 or len(limpio) > 25:
            raise ValueError("El color debe tener entre 3 y 25 caracteres")
        
        if limpio.lower() in COLORES_PROHIBIDOS:
            raise ValueError("Color no permitido")
        
        # Solo letras, espacios y guiones
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ\s\-]+", limpio):
            raise ValueError("El color solo puede contener letras, espacios y guiones")
        
        # Capitalizar correctamente
        object.__setattr__(self, "valor", limpio.title())