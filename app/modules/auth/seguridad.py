"""
Módulo de seguridad para autenticación y autorización de usuarios.
Contiene funciones para crear y validar tokens JWT, así como la configuración.
"""

# Biblioteca estándar
from datetime import datetime, timedelta
import uuid
import logging

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
    eliminar_jti_activacion,
    guardar_jti_reset,
    obtener_jti_reset,
    eliminar_jti_reset
)

# Configurar logging
logger = logging.getLogger(__name__)

# Esquema OAuth2 para validación de tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def crear_token_acceso(usuario_id: str, rol: str) -> str:
    """Genera un token de acceso con expiración."""
    expiracion = datetime.utcnow() + timedelta(minutes=settings.jwt_token_acceso_minutos)
    payload = {
        "sub": usuario_id,
        "rol": rol,
        "exp": expiracion,
        "type": "access"
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    logger.info(f"✅ Token de acceso creado para: {usuario_id}")
    return token

def validar_token_acceso(token: str = Depends(oauth2_scheme)) -> str:
    """Valida un token JWT de acceso y devuelve el ID del usuario."""
    credencial_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autorizado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if esta_en_blacklist(token):
        logger.warning(f"🚫 Token en blacklist utilizado: {token[:20]}...")
        raise credencial_error

    try:
        datos = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        usuario_id: str = datos.get("sub")
        if not usuario_id:
            raise credencial_error
        return usuario_id
    except JWTError as e:
        logger.error(f"❌ Error validando token de acceso: {e}")
        raise credencial_error

def crear_token_activacion(usuario_id: str) -> str:
    """Genera un token de activación de cuenta y guarda su JTI en Redis."""
    expiracion = datetime.utcnow() + timedelta(minutes=settings.email_token_expiracion_minutos)
    jti = str(uuid.uuid4())
    
    payload = {
        "sub": usuario_id,
        "exp": expiracion,
        "jti": jti,
        "type": "activation"
    }
    
    # Calcular TTL para Redis
    ttl = int((expiracion - datetime.utcnow()).total_seconds())
    
    # Guardar JTI en Redis
    guardar_jti_activacion(usuario_id, jti, ttl)
    
    # Crear token
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    
    logger.info(f"✅ Token activación creado para usuario: {usuario_id}")
    logger.debug(f"   JTI: {jti}, TTL: {ttl}s")
    
    return token

def verificar_token_activacion(token: str) -> str:
    """Verifica la validez del token de activación y su JTI."""
    try:
        # Decodificar token
        datos = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        usuario_id: str = datos.get("sub")
        jti_token: str = datos.get("jti")
        token_type: str = datos.get("type")

        logger.info(f"🔍 Verificando token activación:")
        logger.info(f"   Usuario: {usuario_id}")
        logger.info(f"   JTI del token: {jti_token}")
        logger.info(f"   Tipo: {token_type}")

        # Validaciones básicas
        if not usuario_id:
            raise ValueError("Token inválido: falta usuario (sub).")
        
        if not jti_token:
            raise ValueError("Token inválido: falta JTI.")
        
        if token_type != "activation":
            raise ValueError("Token inválido: tipo incorrecto.")

        # Obtener JTI guardado en Redis
        jti_guardado = obtener_jti_activacion(usuario_id)
        
        logger.info(f"   JTI guardado en Redis: {jti_guardado}")
        
        if not jti_guardado:
            raise ValueError("Token de activación no encontrado o ya fue utilizado.")
        
        # Verificar que los JTI coincidan
        if jti_guardado != jti_token:
            raise ValueError("Este enlace ya no es válido. El token ha sido reemplazado por uno más reciente.")

        # IMPORTANTE: Eliminar JTI después de verificar (uso único)
        eliminar_jti_activacion(usuario_id)
        logger.info(f"✅ Token de activación verificado y eliminado para: {usuario_id}")
        
        return usuario_id

    except ExpiredSignatureError:
        logger.warning(f"⏰ Token de activación expirado")
        raise ValueError("El enlace de activación ha expirado. Solicita uno nuevo.")
    except JWTError as e:
        logger.error(f"❌ Error JWT: {e}")
        raise ValueError("Token de activación inválido.")
    except Exception as e:
        logger.error(f"❌ Error inesperado verificando token: {e}")
        raise ValueError("Error interno verificando el token de activación.")

def crear_token_reset(usuario_id: str) -> str:
    """Genera un token para recuperación de contraseña y guarda su JTI en Redis."""
    expiracion = datetime.utcnow() + timedelta(minutes=settings.email_token_expiracion_minutos)
    jti = str(uuid.uuid4())
    
    payload = {
        "sub": usuario_id,
        "exp": expiracion,
        "jti": jti,
        "type": "password_reset"
    }
    
    # Calcular TTL para Redis
    ttl = int((expiracion - datetime.utcnow()).total_seconds())
    
    # Guardar JTI en Redis
    guardar_jti_reset(usuario_id, jti, ttl)
    
    # Crear token
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    
    logger.info(f"✅ Token reset creado para usuario: {usuario_id}")
    logger.debug(f"   JTI: {jti}, TTL: {ttl}s")
    
    return token

def verificar_token_reset(token: str) -> str:
    """Verifica el token de recuperación de contraseña y que no haya sido invalidado."""
    try:
        # Decodificar token
        datos = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        usuario_id: str = datos.get("sub")
        jti_token: str = datos.get("jti")
        token_type: str = datos.get("type")

        logger.info(f"🔍 Verificando token reset:")
        logger.info(f"   Usuario: {usuario_id}")
        logger.info(f"   JTI del token: {jti_token}")
        logger.info(f"   Tipo: {token_type}")

        # Validaciones básicas
        if not usuario_id:
            raise ValueError("Token inválido: falta usuario (sub).")
        
        if not jti_token:
            raise ValueError("Token inválido: falta JTI.")
        
        if token_type != "password_reset":
            raise ValueError("Token inválido: tipo incorrecto.")

        # Obtener JTI guardado en Redis
        jti_guardado = obtener_jti_reset(usuario_id)
        
        logger.info(f"   JTI guardado en Redis: {jti_guardado}")
        
        if not jti_guardado:
            raise ValueError("Este enlace ya fue usado o ha expirado.")
        
        # Verificar que los JTI coincidan
        if jti_guardado != jti_token:
            raise ValueError("Este enlace ya fue usado o reemplazado por uno más reciente.")

        # IMPORTANTE: Eliminar JTI después de verificar (uso único)
        eliminar_jti_reset(usuario_id)
        logger.info(f"✅ Token de reset verificado y eliminado para: {usuario_id}")
        
        return usuario_id

    except ExpiredSignatureError:
        logger.warning(f"⏰ Token de reset expirado")
        raise ValueError("El enlace ha expirado. Solicita uno nuevo.")
    except JWTError as e:
        logger.error(f"❌ Error JWT en reset: {e}")
        raise ValueError("Token de reset inválido.")
    except Exception as e:
        logger.error(f"❌ Error inesperado verificando token reset: {e}")
        raise ValueError("Error interno verificando el token de reset.")

def decodificar_token(token: str) -> dict:
    """Decodifica un JWT y devuelve su payload si es válido."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as e:
        logger.error(f"❌ Error decodificando token: {e}")
        raise