'''
    Objeto de valor para el nombre de una pertenencia.
    Valida que el nombre sea descriptivo y tenga al menos 3 caracteres.
'''
import re
from dataclasses import dataclass

PALABRAS_PROHIBIDAS = {"objeto", "cosa", "item", "test", "default"}

@dataclass(frozen=True)
class NombrePertenencia:
    valor: str

    def __post_init__(self):
        limpio = self.valor.strip()
        if len(limpio) < 3 or len(limpio) > 50:
            raise ValueError("El nombre debe tener entre 3 y 50 caracteres.")
        if limpio.lower() in PALABRAS_PROHIBIDAS:
            raise ValueError("El nombre es demasiado genérico o no permitido.")
        if re.search(r"(.)\1{3,}", limpio):
            raise ValueError("El nombre no puede tener más de 3 caracteres repetidos consecutivos.")
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s\-]+", limpio):
            raise ValueError("El nombre solo puede contener letras, números, espacios y guiones.")
        object.__setattr__(self, "valor", limpio.title())