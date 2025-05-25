"""
    Define los esquemas Pydantic para la API de usuarios:

    - UsuarioCreate: datos de entrada necesarios para registrar un nuevo usuario.
    - UsuarioRead: datos de salida que se envían al cliente para representar un usuario existente.
"""

# Librerías de terceros
from pydantic import BaseModel

# Objetos de valor del dominio
from app.modules.autenticacion.domain.objetos_de_valor.enums.tipo_documento import TipoDocumento
from app.modules.autenticacion.domain.objetos_de_valor.enums.rol_usuario import RolUsuario

class UsuarioCreate(BaseModel):
    tipo_documento: TipoDocumento
    numero_documento: str
    nombres: str
    apellidos: str
    correo_institucional: str
    contrasena: str
    rol: RolUsuario

class UsuarioRead(BaseModel):
    tipo_documento: str
    numero_documento: str
    nombres: str
    apellidos: str
    correo_institucional: str
    activo: bool = False
    rol: str

    @classmethod
    def from_domain(cls, u):
        return cls(
            tipo_documento=u.tipo_documento.name,
            numero_documento=u.numero_documento.valor,
            nombres=u.nombres.valor,
            apellidos=u.apellidos.valor, 
            correo_institucional=u.correo_institucional.valor,
            activo=u.activo,
            rol=u.rol.value

        )
