'''
    Servicio de autenticación y autorización.
'''

# Importaciones de FastAPI
from fastapi import Depends, HTTPException, status

# Servicios de autenticación y gestión de tokens
from app.modules.auth.seguridad import (
    crear_token_acceso,
    validar_token_acceso,
    crear_token_activacion,
    verificar_token_activacion,
    crear_token_reset,
    verificar_token_reset,
)

# Caso de uso de autenticación
from app.modules.autenticacion.application.casos_de_uso.autenticar_usuario import autenticar_usuario

# Repositorios e infraestructura de datos
from app.modules.autenticacion.infrastructure.repositorios.repositorio import RepositorioUsuariosBD

# Envío de correos
from app.modules.autenticacion.infrastructure.email.sender import enviar_correo_activacion
from app.modules.autenticacion.infrastructure.email.sender_resetear_contrasena import enviar_correo_reset

# Cifrador de contraseñas
from app.modules.autenticacion.infrastructure.cifrador_contrasena.cifrador import hash_password

# Objetos de valor del dominio
from app.modules.autenticacion.domain.objetos_de_valor.contrasena import Contrasena

# Dependencias de base de datos
from app.core.dependencias.dependencias import get_db

class ServicioAuth:
    """Orquesta login, JWT y todo el flujo de activación y recuperación."""

    def __init__(self, repo=None):
        self.repo = repo or RepositorioUsuariosBD(next(get_db()))


    def login(self, tipo_doc, numero_doc, contrasena_plana) -> str:
        try:
            usuario = autenticar_usuario(
                self.repo, tipo_doc, numero_doc, contrasena_plana
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cuenta no está activada",
            )

        return crear_token_acceso(usuario.numero_documento.valor, usuario.rol.value)

    def obtener_usuario_actual(self, usuario_id: str = Depends(validar_token_acceso)):
        usuario = self.repo.obtener_por_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )
        return usuario

    async def enviar_activacion(
        self, numero_documento: str, nombre_usuario: str, email: str
    ) -> None:

        token = crear_token_activacion(numero_documento)
        await enviar_correo_activacion(
            email_to=email,
            numero_documento=numero_documento,
            nombre_usuario=nombre_usuario,
        )

    def activar_cuenta(self, token: str) -> str:
        try:
            user_id = verificar_token_activacion(token)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        usuario = self.repo.obtener_por_id(user_id)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if usuario.activo:
            raise HTTPException(status_code=400, detail="Cuenta ya activada")

        usuario.activo = True
        self.repo.actualizar(usuario)
        return user_id

    async def enviar_reset_contrasena(
        self, numero_documento: str, nombre_usuario: str, email: str
    ) -> None:
        """
        Genera el JWT para reset de contraseña y lo envía por correo.
        """
        token = crear_token_reset(numero_documento)
        await enviar_correo_reset(
            email_to=email,
            numero_documento=numero_documento,
            nombre_usuario=nombre_usuario,
        )

    def reset_contrasena(self, token: str, nueva_contrasena: str) -> None:
        """
        Valida el JWT de reset, hashea la nueva contraseña y actualiza en BD.
        """
        try:
            user_id = verificar_token_reset(token)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        usuario = self.repo.obtener_por_id(user_id)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        usuario.contrasena = Contrasena(hash_password(nueva_contrasena))
        self.repo.actualizar(usuario)


    