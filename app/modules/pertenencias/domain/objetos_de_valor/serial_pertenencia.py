'''
    Objeto de valor para el serial o identificador único de una pertenencia.
    El serial es opcional, pero si se provee debe cumplir reglas de seguridad.
'''
import re
from dataclasses import dataclass

PALABRAS_PROHIBIDAS = {"admin", "root", "null", "test", "serial", "default"}
PATRONES_PROHIBIDOS = [r"1234+", r"0000+", r"1111+", r"abcd+", r"qwer+"]

@dataclass(frozen=True)
class SerialPertenencia:
    valor: str

    def __post_init__(self):
        limpio = self.valor.strip()
        if limpio:
            if not re.fullmatch(r"[A-Za-z0-9\-]{4,30}", limpio):
                raise ValueError("El serial debe tener entre 4 y 30 caracteres alfanuméricos o guiones.")
            if limpio.lower() in PALABRAS_PROHIBIDAS:
                raise ValueError("El serial contiene una palabra prohibida.")
            if len(set(limpio)) == 1:
                raise ValueError("El serial no puede tener todos los caracteres iguales.")
            if re.search(r"[O0Il]", limpio):
                raise ValueError("El serial no puede contener caracteres ambiguos como O, 0, I, l.")
            for patron in PATRONES_PROHIBIDOS:
                if re.fullmatch(patron, limpio.lower()):
                    raise ValueError("El serial contiene un patrón demasiado simple o común.")
            limpio = limpio.upper()
        object.__setattr__(self, "valor", limpio)