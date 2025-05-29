'''
    Objeto de valor para la foto de la pertenencia.
    Puede ser una URL o ruta local válida.
'''
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class FotoPertenencia:
    valor: str

    def __post_init__(self):
        limpio = self.valor.strip()
        if not limpio:
            raise ValueError("La foto de la pertenencia no puede estar vacía.")
        # Solo permitir imágenes jpg, jpeg, png, webp
        if not re.match(r"^https?://.*\.(jpg|jpeg|png|webp)$", limpio, re.IGNORECASE) and \
           not re.match(r"^[\w\-/\\\.]+(\.jpg|\.jpeg|\.png|\.webp)$", limpio, re.IGNORECASE):
            raise ValueError("La foto debe ser una URL o ruta local válida a una imagen (jpg, jpeg, png, webp).")
        object.__setattr__(self, "valor", limpio)