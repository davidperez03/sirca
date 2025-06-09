"""
Objeto de valor para el modelo del vehículo.
"""
import re
from dataclasses import dataclass

MODELOS_PROHIBIDOS = {"test", "demo", "null", "undefined", "admin", "modelo"}

@dataclass(frozen=True)
class ModeloVehiculo:
    valor: str

    def __post_init__(self):
        limpio = self.valor.strip() if self.valor else ""
        
        if not limpio:
            raise ValueError("El modelo es obligatorio")
        
        if len(limpio) < 1 or len(limpio) > 40:
            raise ValueError("El modelo debe tener entre 1 y 40 caracteres")
        
        if limpio.lower() in MODELOS_PROHIBIDOS:
            raise ValueError("Modelo no permitido")
        
        # Letras, números, espacios, guiones y puntos
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s\-\.]+", limpio):
            raise ValueError("El modelo solo puede contener letras, números, espacios, guiones y puntos")
        
        # Capitalizar correctamente
        object.__setattr__(self, "valor", limpio.title())