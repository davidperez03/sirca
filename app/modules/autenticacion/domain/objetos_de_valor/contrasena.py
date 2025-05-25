'''
    Se define el objeto de valor para la contraseña.
    Este objeto de valor es inmutable y se utiliza para representar la contraseña de un usuario.
    Se utiliza un hash para almacenar la contraseña de forma segura.
'''
# Biblioteca estándar
from dataclasses import dataclass 

@dataclass(frozen=True) 
class Contrasena:
    hash: str

    def __post_init__(self):
        if not self.hash or not self.hash.strip():
            raise ValueError("El hash de la contraseña no puede estar vacío.")
