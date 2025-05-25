"""
Módulo de seguridad para autenticación y autorización de usuarios.
Contiene funciones para crear y validar tokens JWT, así como la configuración.
"""

# Biblioteca estándar
from datetime import datetime, timedelta
import uuid

# Librerías de terceros
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Configuración principal
from app.core.config import settings

# Servicios de autenticación y blacklist
from app.modules.auth.blacklist import (
    esta_en_blacklist,
    guardar_jti_activacion,
    obtener_jti_activacion,
    guardar_jti_reset,
    obtener_jti_reset
)

# Esquema OAuth2 para validación de tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/usuarios/login")

def crear_token_acceso(usuario_id: str, rol: str) -> str:
    """Genera un token de acceso con expiración."""
    expiracion = datetime.utcnow() + timedelta(minutes=settings.jwt_token_acceso_minutos)
    payload = {
        "sub": usuario_id,
        "rol": rol,
        "exp": expiracion
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def validar_token_acceso(token: str = Depends(oauth2_scheme)) -> str:
    """Valida un token JWT de acceso y devuelve el ID del usuario."""
    credencial_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autorizado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if esta_en_blacklist(token):
        raise credencial_error

    try:
        datos = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        usuario_id: str = datos.get("sub")
        if not usuario_id:
            raise credencial_error
        return usuario_id
    except JWTError:
        raise credencial_error


def crear_token_activacion(usuario_id: str) -> str:
    """Genera un token de activación de cuenta y guarda su jti en Redis."""
    expiracion = datetime.utcnow() + timedelta(minutes=settings.email_token_expiracion_minutos)
    jti = str(uuid.uuid4())
    payload = {
        "sub": usuario_id,
        "exp": expiracion,
        "jti": jti
    }
    ttl = int((expiracion - datetime.utcnow()).total_seconds())
    guardar_jti_activacion(usuario_id, jti, ttl)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def verificar_token_activacion(token: str) -> str:
    """Verifica la validez del token de activación y su jti."""
    try:
        datos = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        usuario_id: str = datos.get("sub")
        jti_token: str = datos.get("jti")

        if not usuario_id or not jti_token:
            raise ValueError("Token inválido.")

        jti_guardado = obtener_jti_activacion(usuario_id)
        if jti_guardado != jti_token:
            raise ValueError("Este enlace ya no es válido. Solicita uno nuevo.")

        return usuario_id

    except ExpiredSignatureError:
        raise ValueError("El enlace de activación ha expirado.")
    except JWTError:
        raise ValueError("Token inválido.")


def crear_token_reset(usuario_id: str) -> str:
    """Genera un token para recuperación de contraseña y guarda su jti en Redis."""
    expiracion = datetime.utcnow() + timedelta(minutes=settings.email_token_expiracion_minutos)
    jti = str(uuid.uuid4())
    payload = {
        "sub": usuario_id,
        "exp": expiracion,
        "jti": jti
    }
    ttl = int((expiracion - datetime.utcnow()).total_seconds())
    guardar_jti_reset(usuario_id, jti, ttl)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def verificar_token_reset(token: str) -> str:
    """Verifica el token de recuperación de contraseña y que no haya sido invalidado."""
    try:
        datos = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        usuario_id: str = datos.get("sub")
        jti_token: str = datos.get("jti")

        if not usuario_id or not jti_token:
            raise ValueError("Token inválido.")

        jti_guardado = obtener_jti_reset(usuario_id)
        if jti_guardado != jti_token:
            raise ValueError("Este enlace ya fue usado o reemplazado.")

        return usuario_id

    except ExpiredSignatureError:
        raise ValueError("El enlace ha expirado.")
    except JWTError:
        raise ValueError("Token inválido.")


def decodificar_token(token: str) -> dict:
    """Decodifica un JWT y devuelve su payload si es válido."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        raise
