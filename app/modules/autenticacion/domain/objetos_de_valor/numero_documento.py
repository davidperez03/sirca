'''
    Objeto de valor para el número de documento de identificación.
    Este objeto de valor es inmutable y se utiliza para representar el número de documento de un usuario.
    Se utiliza para validar y normalizar el número de documento, asegurando que cumpla con ciertas reglas de formato.
'''

# Biblioteca estándar
from dataclasses import dataclass, field
import re

# Objetos de valor del dominio
from app.modules.autenticacion.domain.objetos_de_valor.enums.tipo_documento import TipoDocumento

@dataclass(frozen=True)
class NumeroDocumento:
    tipo_documento: TipoDocumento
    valor: str = field(repr=False)

    def __post_init__(self):
        limpio = self.valor.strip()

        # Verificar que no esté vacío
        if not limpio:
            raise ValueError("El número de documento no puede estar vacío.")

        # Validación para CC, TI, CE y PPT
        if self.tipo_documento in {TipoDocumento.CC, TipoDocumento.TI, TipoDocumento.CE, TipoDocumento.PPT}:
            # Sólo dígitos
            if not limpio.isdigit():
                raise ValueError(
                    f"Para '{self.tipo_documento.value}', el documento debe contener solo dígitos."
                )
            # Longitud mínima y máxima
            longitud = len(limpio)
            if longitud < 6:
                faltan = 6 - longitud
                raise ValueError(
                    f"El documento es muy corto ({longitud} dígitos); faltan {faltan} para el mínimo de 6."
                )
            if longitud > 12:
                sobran = longitud - 12
                raise ValueError(
                    f"El documento es muy largo ({longitud} dígitos); excede en {sobran} del máximo de 12."
                )
            # No empezar con cero
            if limpio.startswith("0"):
                raise ValueError("El número de documento no puede empezar con cero.")

        # Validación para pasaporte
        elif self.tipo_documento == TipoDocumento.PAS:
            if not re.fullmatch(r"[A-Za-z0-9]{6,12}", limpio):
                raise ValueError(
                    "Para 'Pasaporte', debe usar entre 6 y 12 caracteres alfanuméricos (letras y números)."
                )

        # Cualquier otro tipo no soportado
        else:
            raise ValueError(
                f"Tipo de documento '{self.tipo_documento.value}' no está soportado."
            )

        # Asignamos el valor limpio
        object.__setattr__(self, 'valor', limpio)
