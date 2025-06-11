'''
    Servicio de autenticación y autorización.
'''

import logging

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

# Configurar logging
logger = logging.getLogger(__name__)

class ServicioAuth:
    """Orquesta login, JWT y todo el flujo de activación y recuperación."""

    def __init__(self, repo=None):
        self.repo = repo or RepositorioUsuariosBD(next(get_db()))

    def login(self, tipo_doc, numero_doc, contrasena_plana) -> str:
        """Realiza el login del usuario y retorna el token de acceso"""
        try:
            usuario = autenticar_usuario(
                self.repo, tipo_doc, numero_doc, contrasena_plana
            )
        except ValueError as e:
            logger.warning(f"❌ Intento de login fallido: {numero_doc} - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not usuario.activo:
            logger.warning(f"❌ Intento de login con cuenta inactiva: {numero_doc}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cuenta no está activada",
            )

        token = crear_token_acceso(usuario.numero_documento.valor, usuario.rol.value)
        logger.info(f"✅ Login exitoso: {numero_doc}")
        return token

    def obtener_usuario_actual(self, usuario_id: str = Depends(validar_token_acceso)):
        """Obtiene el usuario actual basado en el token de acceso"""
        usuario = self.repo.obtener_por_id(usuario_id)
        if not usuario:
            logger.error(f"❌ Usuario no encontrado: {usuario_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )
        return usuario

    async def enviar_activacion(
        self, numero_documento: str, nombre_usuario: str, email: str
    ) -> None:
        """Crea token de activación y envía correo"""
        
        logger.info(f"📧 Enviando correo de activación a: {email}")
        
        # Crear token con JTI único
        token = crear_token_activacion(numero_documento)
        
        # Enviar correo
        await enviar_correo_activacion(
            email_to=email,
            numero_documento=numero_documento,
            nombre_usuario=nombre_usuario,
        )
        
        logger.info(f"✅ Correo de activación enviado: {email}")

    def activar_cuenta(self, token: str) -> str:
        """Activa una cuenta usando el token de activación"""
        try:
            # Verificar token y obtener usuario_id
            user_id = verificar_token_activacion(token)
        except ValueError as e:
            logger.error(f"❌ Error activando cuenta: {e}")
            raise HTTPException(status_code=400, detail=str(e))

        # Buscar usuario
        usuario = self.repo.obtener_por_id(user_id)
        if not usuario:
            logger.error(f"❌ Usuario no encontrado para activación: {user_id}")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        if usuario.activo:
            logger.warning(f"⚠️ Intento de activar cuenta ya activa: {user_id}")
            raise HTTPException(status_code=400, detail="Cuenta ya activada")

        # Activar cuenta
        usuario.activo = True
        self.repo.actualizar(usuario)
        
        logger.info(f"✅ Cuenta activada exitosamente: {user_id}")
        return user_id

    async def enviar_reset_contrasena(
        self, numero_documento: str, nombre_usuario: str, email: str
    ) -> None:
        """Genera el JWT para reset de contraseña y lo envía por correo."""
        
        logger.info(f"📧 Enviando correo de reset a: {email}")
        
        # Crear token con JTI único
        token = crear_token_reset(numero_documento)
        
        # Enviar correo
        await enviar_correo_reset(
            email_to=email,
            numero_documento=numero_documento,
            nombre_usuario=nombre_usuario,
        )
        
        logger.info(f"✅ Correo de reset enviado: {email}")

    def reset_contrasena(self, token: str, nueva_contrasena: str) -> None:
        """Valida el JWT de reset, hashea la nueva contraseña y actualiza en BD."""
        
        try:
            # Verificar token y obtener usuario_id
            user_id = verificar_token_reset(token)
        except ValueError as e:
            logger.error(f"❌ Error en reset de contraseña: {e}")
            raise HTTPException(status_code=400, detail=str(e))

        # Buscar usuario
        usuario = self.repo.obtener_por_id(user_id)
        if not usuario:
            logger.error(f"❌ Usuario no encontrado para reset: {user_id}")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Actualizar contraseña
        usuario.contrasena = Contrasena(hash_password(nueva_contrasena))
        self.repo.actualizar(usuario)
        
        logger.info(f"✅ Contraseña reseteada exitosamente: {user_id}")