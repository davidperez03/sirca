'''
    Blacklist de tokens JWT
    este módulo se encarga de gestionar la blacklist de tokens JWT, almacenando los tokens revocados en Redis.
    El módulo proporciona dos funciones principales:
    1. agregar_token_a_blacklist: agrega un token a la blacklist con un tiempo de expiración específico.
    2. esta_en_blacklist: verifica si un token está en la blacklist.
'''

# Librerías de terceros
import redis

# Configuración principal
from app.core.config import settings

from typing import Optional

r = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    decode_responses=True
)

def agregar_token_a_blacklist(token: str, exp_seconds: int):
    r.setex(f"blacklist:{token}", exp_seconds, "blacklisted")

def esta_en_blacklist(token: str) -> bool:
    return r.exists(f"blacklist:{token}") == 1

def guardar_jti_activacion(user_id: str, jti: str, ttl: int):
    r.setex(f"jwt:activacion:{user_id}", ttl, jti)

def obtener_jti_activacion(user_id: str) -> Optional[str]:
    """Devuelve el JTI actual almacenado para activación de cuenta."""
    return r.get(f"jwt:activacion:{user_id}")

def guardar_jti_reset(user_id: str, jti: str, ttl: int):
    r.setex(f"jwt:reset:{user_id}", ttl, jti)

def obtener_jti_reset(user_id: str) -> Optional[str]:
    return r.get(f"jwt:reset:{user_id}")