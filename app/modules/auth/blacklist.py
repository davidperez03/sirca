import redis
from typing import Optional

# Configuración principal
from app.core.config import settings

def create_redis_connection():
    """Crea conexión a Redis con manejo de errores"""
    try:
        redis_config = settings.get_redis_config()
        
        if "url" in redis_config:
            r = redis.from_url(redis_config["url"])
        else:

            r = redis.Redis(**redis_config)
        
        r.ping()
        return r
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
        return DummyRedis()

class DummyRedis:
    """Cliente Redis dummy para cuando no hay conexión disponible"""
    def setex(self, key, time, value):
        print(f"⚠️ Redis no disponible: setex({key}, {time}, {value})")
        return True
    
    def get(self, key):
        print(f"⚠️ Redis no disponible: get({key})")
        return None
    
    def exists(self, key):
        print(f"⚠️ Redis no disponible: exists({key})")
        return 0

# Crear conexión global
r = create_redis_connection()

def agregar_token_a_blacklist(token: str, exp_seconds: int):
    try:
        r.setex(f"blacklist:{token}", exp_seconds, "blacklisted")
    except Exception as e:
        print(f"⚠️ Error en blacklist: {e}")

def esta_en_blacklist(token: str) -> bool:
    try:
        return r.exists(f"blacklist:{token}") == 1
    except Exception as e:
        print(f"⚠️ Error verificando blacklist: {e}")
        return False

def guardar_jti_activacion(user_id: str, jti: str, ttl: int):
    try:
        r.setex(f"jwt:activacion:{user_id}", ttl, jti)
    except Exception as e:
        print(f"⚠️ Error guardando JTI activación: {e}")

def obtener_jti_activacion(user_id: str) -> Optional[str]:
    try:
        return r.get(f"jwt:activacion:{user_id}")
    except Exception as e:
        print(f"⚠️ Error obteniendo JTI activación: {e}")
        return None

def guardar_jti_reset(user_id: str, jti: str, ttl: int):
    try:
        r.setex(f"jwt:reset:{user_id}", ttl, jti)
    except Exception as e:
        print(f"⚠️ Error guardando JTI reset: {e}")

def obtener_jti_reset(user_id: str) -> Optional[str]:
    try:
        return r.get(f"jwt:reset:{user_id}")
    except Exception as e:
        print(f"⚠️ Error obteniendo JTI reset: {e}")
        return None