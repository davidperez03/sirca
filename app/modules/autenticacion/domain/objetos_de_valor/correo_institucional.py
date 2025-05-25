'''
    Objeto de valor para el correo institucional.
    Se utiliza para validar el formato y dominio del correo electrónico.
    Se asegura de que el correo electrónico tenga un formato válido y que pertenezca a un dominio institucional específico.
'''

# Biblioteca estándar
import re
from dataclasses import dataclass
from app.modules.autenticacion.domain.constantes.dominios_correo import DOMINIOS_CORREO_PERMITIDOS


@dataclass(frozen=True)
class CorreoInstitucional:
    valor: str

    def __post_init__(self):
        email = self.valor.strip().lower()
        # 1) Formato básico de email
        if not re.fullmatch(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", email):
            raise ValueError("Formato de correo inválido.")
        
        if not email.endswith(DOMINIOS_CORREO_PERMITIDOS):
            dominios_str = ', '.join(DOMINIOS_CORREO_PERMITIDOS)
            raise ValueError(f"El correo debe terminar en: {dominios_str}.")