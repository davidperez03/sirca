'''
    Objeto de valor que representa un nombre propio.
    Este objeto de valor es inmutable y se utiliza para representar el nombre de un usuario.
    Se utiliza para validar y normalizar el nombre propio, asegurando que cumpla con ciertas reglas de formato.
'''

# Biblioteca estándar
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class NombrePropio:
    valor: str

    def __post_init__(self):
        limpio = self.valor.strip()

        # 1) Debe tener al menos dos caracteres
        if len(limpio) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres.")

        # 2) Sólo letras, espacios y guiones medios (p. ej. “María-José”)
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+(?:[-\s][A-Za-zÁÉÍÓÚáéíóúÑñ]+)*", limpio):
            raise ValueError(
                "El nombre sólo puede contener letras, espacios o guiones medios, "
                "y no puede empezar o terminar con un espacio o guión."
            )

        # 3) Normalizamos espacios internos y capitalizamos cada palabra
        partes = re.split(r"[\s-]+", limpio)
        normalizado = " ".join(p.capitalize() for p in partes)

        # 4) Si el nombre original tenía guiones, los volvemos a poner
        if "-" in limpio:
            hyphens = []
            idx = 0
            for match in re.finditer(r"[-\s]+", limpio):
                hyphens.append((match.start(), match.group()))
            # Reconstrucción sencilla: reemplazamos los espacios por guiones donde los había
            normalizado = re.sub(r"\s", "-", normalizado)

        object.__setattr__(self, "valor", normalizado)
