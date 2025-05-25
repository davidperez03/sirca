''''
Módulo de la entidad Usuario.
Este módulo contiene la definición de la entidad Usuario, que representa a un usuario en el sistema.'''

# Biblioteca estándar
from dataclasses import dataclass

# Objetos de valor del dominio
from app.modules.autenticacion.domain.objetos_de_valor.enums.tipo_documento import TipoDocumento
from app.modules.autenticacion.domain.objetos_de_valor.enums.rol_usuario import RolUsuario
from app.modules.autenticacion.domain.objetos_de_valor.numero_documento import NumeroDocumento
from app.modules.autenticacion.domain.objetos_de_valor.nombre_propio import NombrePropio
from app.modules.autenticacion.domain.objetos_de_valor.correo_institucional import CorreoInstitucional
from app.modules.autenticacion.domain.objetos_de_valor.contrasena import Contrasena

@dataclass
class Usuario:
    tipo_documento: TipoDocumento
    numero_documento: NumeroDocumento
    nombres: NombrePropio
    apellidos: NombrePropio
    correo_institucional: CorreoInstitucional
    contrasena: Contrasena
    rol: RolUsuario 
    activo: bool = False