import redis
from typing import Optional
import logging

# Configuración principal
from app.core.config import settings

# Configurar logging
logger = logging.getLogger(__name__)

def create_redis_connection():
    """Crea conexión a Redis con manejo de errores"""
    try:
        redis_config = settings.get_redis_config()
        
        if "url" in redis_config:
            r = redis.from_url(redis_config["url"], decode_responses=True)
        else:
            # decode_responses ya viene en redis_config
            r = redis.Redis(**redis_config)
        
        r.ping()
        logger.info("✅ Redis conectado correctamente")
        return r
    except Exception as e:
        logger.error(f"❌ Error conectando a Redis: {e}")
        return DummyRedis()


class DummyRedis:
    """Cliente Redis dummy para cuando no hay conexión disponible"""
    def setex(self, key, time, value):
        logger.warning(f"⚠️ Redis no disponible: setex({key}, {time}, {value})")
        return True
    
    def get(self, key):
        logger.warning(f"⚠️ Redis no disponible: get({key})")
        return None
    
    def exists(self, key):
        logger.warning(f"⚠️ Redis no disponible: exists({key})")
        return 0
    
    def ping(self):
        return True
    
    def delete(self, key):
        logger.warning(f"⚠️ Redis no disponible: delete({key})")
        return 0
    
    def keys(self, pattern):
        logger.warning(f"⚠️ Redis no disponible: keys({pattern})")
        return []

# Crear conexión global
r = create_redis_connection()

def get_redis():
    """Retorna la instancia de Redis global"""
    return r

def agregar_token_a_blacklist(token: str, exp_seconds: int):
    """Agrega un token a la blacklist"""
    try:
        result = r.setex(f"blacklist:{token}", exp_seconds, "blacklisted")
        logger.info(f"✅ Token agregado a blacklist: {token[:20]}...")
        return result
    except Exception as e:
        logger.error(f"⚠️ Error en blacklist: {e}")
        return False

def esta_en_blacklist(token: str) -> bool:
    """Verifica si un token está en la blacklist"""
    try:
        result = r.exists(f"blacklist:{token}") == 1
        if result:
            logger.info(f"🚫 Token encontrado en blacklist: {token[:20]}...")
        return result
    except Exception as e:
        logger.error(f"⚠️ Error verificando blacklist: {e}")
        return False

def guardar_jti_activacion(user_id: str, jti: str, ttl: int):
    """Guarda JTI para token de activación"""
    try:
        key = f"jwt:activacion:{user_id}"
        result = r.setex(key, ttl, jti)
        logger.info(f"✅ JTI activación guardado: {user_id} -> {jti[:10]}...")
        logger.debug(f"   Key: {key}, TTL: {ttl}s")
        return result
    except Exception as e:
        logger.error(f"⚠️ Error guardando JTI activación: {e}")
        return False

def obtener_jti_activacion(user_id: str) -> Optional[str]:
    """Obtiene JTI guardado para activación"""
    try:
        key = f"jwt:activacion:{user_id}"
        result = r.get(key)
        
        if result:
            logger.info(f"✅ JTI activación encontrado: {user_id}")
            logger.debug(f"   Key: {key}, JTI: {result}")
        else:
            logger.warning(f"⚠️ JTI activación NO encontrado: {user_id}")
            logger.debug(f"   Key buscada: {key}")
            
            # Debug: Listar claves similares
            try:
                all_activation_keys = r.keys("jwt:activacion:*")
                logger.debug(f"   Claves existentes: {all_activation_keys}")
            except:
                pass
        
        return result
    except Exception as e:
        logger.error(f"⚠️ Error obteniendo JTI activación: {e}")
        return None

def eliminar_jti_activacion(user_id: str):
    """Elimina JTI de activación después de usar"""
    try:
        key = f"jwt:activacion:{user_id}"
        result = r.delete(key)
        logger.info(f"✅ JTI activación eliminado: {user_id}")
        logger.debug(f"   Key eliminada: {key}, Resultado: {result}")
        return result
    except Exception as e:
        logger.error(f"⚠️ Error eliminando JTI activación: {e}")
        return 0

def guardar_jti_reset(user_id: str, jti: str, ttl: int):
    """Guarda JTI para token de reset"""
    try:
        key = f"jwt:reset:{user_id}"
        result = r.setex(key, ttl, jti)
        logger.info(f"✅ JTI reset guardado: {user_id} -> {jti[:10]}...")
        logger.debug(f"   Key: {key}, TTL: {ttl}s")
        return result
    except Exception as e:
        logger.error(f"⚠️ Error guardando JTI reset: {e}")
        return False

def obtener_jti_reset(user_id: str) -> Optional[str]:
    """Obtiene JTI guardado para reset"""
    try:
        key = f"jwt:reset:{user_id}"
        result = r.get(key)
        
        if result:
            logger.info(f"✅ JTI reset encontrado: {user_id}")
            logger.debug(f"   Key: {key}, JTI: {result}")
        else:
            logger.warning(f"⚠️ JTI reset NO encontrado: {user_id}")
            logger.debug(f"   Key buscada: {key}")
        
        return result
    except Exception as e:
        logger.error(f"⚠️ Error obteniendo JTI reset: {e}")
        return None

def eliminar_jti_reset(user_id: str):
    """Elimina JTI de reset después de usar"""
    try:
        key = f"jwt:reset:{user_id}"
        result = r.delete(key)
        logger.info(f"✅ JTI reset eliminado: {user_id}")
        logger.debug(f"   Key eliminada: {key}, Resultado: {result}")
        return result
    except Exception as e:
        logger.error(f"⚠️ Error eliminando JTI reset: {e}")
        return 0