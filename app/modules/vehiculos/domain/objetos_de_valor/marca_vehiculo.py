"""
Objeto de valor para la marca del vehículo.
"""
import re
from dataclasses import dataclass

MARCAS_PROHIBIDAS = {"test", "demo", "null", "undefined", "admin", "marca"}

@dataclass(frozen=True)
class MarcaVehiculo:
    valor: str

    def __post_init__(self):
        limpio = self.valor.strip() if self.valor else ""
        
        if not limpio:
            raise ValueError("La marca es obligatoria")
        
        if len(limpio) < 2 or len(limpio) > 30:
            raise ValueError("La marca debe tener entre 2 y 30 caracteres")
        
        if limpio.lower() in MARCAS_PROHIBIDAS:
            raise ValueError("Marca no permitida")
        
        # Solo letras, números, espacios y guiones
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s\-]+", limpio):
            raise ValueError("La marca solo puede contener letras, números, espacios y guiones")
        
        # Capitalizar correctamente
        object.__setattr__(self, "valor", limpio.title())