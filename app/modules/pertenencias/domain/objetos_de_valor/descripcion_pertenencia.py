'''
    Objeto de valor para la descripción de una pertenencia.
    Permite texto libre hasta 200 caracteres.
'''
from dataclasses import dataclass

@dataclass(frozen=True)
class DescripcionPertenencia:
    valor: str

    def __post_init__(self):
        limpio = self.valor.strip()
        if limpio and len(limpio) < 5:
            raise ValueError("La descripción debe tener al menos 5 caracteres si se proporciona.")
        if len(limpio) > 200:
            raise ValueError("La descripción no puede superar los 200 caracteres.")
        object.__setattr__(self, "valor", limpio)