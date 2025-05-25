"""
    Valida la nueva contraseña mediante el servicio de dominio y actualiza al usuario.
"""

# Dominio
from app.modules.autenticacion.domain.servicios.validador_contrasena import ValidadorContrasena
from app.modules.autenticacion.domain.entidades.usuario import Usuario
from app.modules.autenticacion.domain.objetos_de_valor.contrasena import Contrasena

# Infraestructura
from app.modules.autenticacion.infrastructure.cifrador_contrasena.cifrador import hash_password

def resetear_contrasena(usuario: Usuario, nueva_contrasena_plana: str) -> None:

    # 1) Validar primero usando el servicio
    ValidadorContrasena.validar(nueva_contrasena_plana)

    # 2) Si pasa, crear objeto de valor Contrasena
    nueva_contrasena = Contrasena(hash_password(nueva_contrasena_plana))

    # 3) Actualizar
    usuario.contrasena = nueva_contrasena
