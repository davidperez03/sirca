# app/core/dependencias/dependencias.py - VERSIÓN CORREGIDA para Railway

'''
    Configuración de la aplicación FastAPI con manejo robusto de errores para Railway.
    Soluciona problemas de conexión PostgreSQL y incluye fallback a SQLite.
'''

# Librerías de terceros
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool, NullPool
import os
import logging
import time

# Configuración principal
from app.core.config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_railway_engine():
    """Crea engine con configuración específica para Railway"""
    database_url = str(settings.database_url)
    is_postgresql = "postgresql" in database_url.lower()
    is_railway = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"))
    
    logger.info(f"🔧 Configurando BD - PostgreSQL: {is_postgresql}, Railway: {is_railway}")
    logger.info(f"📍 Database URL: {database_url[:50]}...")
    
    if is_postgresql and is_railway:
        # Configuración específica para PostgreSQL en Railway
        try:
            engine_config = {
                "pool_pre_ping": True,
                "pool_recycle": 300,      # 5 minutos (más corto para Railway)
                "pool_size": 5,           # Menos conexiones para Railway
                "max_overflow": 10,       # Menos overflow
                "pool_timeout": 20,       # Timeout más corto
                "echo": False,
                "connect_args": {
                    "connect_timeout": 10,
                    "sslmode": "prefer",  # Cambiar de "require" a "prefer"
                    "application_name": "SIRCA-Railway",
                    "options": "-c statement_timeout=30s"
                }
            }
            
            logger.info("🚂 Aplicando configuración Railway PostgreSQL...")
            engine = create_engine(database_url, **engine_config)
            
            # Test de conexión inmediato
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).fetchone()
                logger.info(f"✅ PostgreSQL conectado: {result[0]}")
                
            return engine
            
        except Exception as e:
            logger.error(f"❌ Error conectando PostgreSQL: {str(e)}")
            # Intentar con configuración más simple
            return create_simple_postgres_engine(database_url)
    
    elif is_postgresql:
        # PostgreSQL local/desarrollo
        return create_simple_postgres_engine(database_url)
    
    else:
        # SQLite fallback
        logger.info("🔧 Usando SQLite como fallback")
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
            echo=False
        )

def create_simple_postgres_engine(database_url):
    """Configuración PostgreSQL simplificada para troubleshooting"""
    try:
        logger.info("🔄 Intentando configuración PostgreSQL simplificada...")
        
        # Configuración mínima
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False,
            connect_args={
                "connect_timeout": 30,
            }
        )
        
        # Test de conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            logger.info(f"✅ PostgreSQL simple conectado: {result[0]}")
            
        return engine
        
    except Exception as e:
        logger.error(f"❌ Error en configuración simple: {str(e)}")
        raise e

def create_fallback_engine():
    """Engine de emergencia con SQLite"""
    logger.warning("⚠️ Usando SQLite de emergencia")
    
    # Crear SQLite en memoria como último recurso
    sqlite_url = "sqlite:///./emergency.db"
    
    return create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        echo=False
    )

# Intentar crear engine con reintentos
def create_engine_with_retry(max_retries=3):
    """Crear engine con reintentos y fallback"""
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 Intento de conexión {attempt + 1}/{max_retries}")
            engine = create_railway_engine()
            
            # Verificar que funciona
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                
            logger.info("✅ Engine creado exitosamente")
            return engine
            
        except Exception as e:
            logger.error(f"❌ Intento {attempt + 1} falló: {str(e)}")
            
            if attempt < max_retries - 1:
                sleep_time = 2 ** attempt  # Backoff exponencial
                logger.info(f"⏳ Esperando {sleep_time}s antes del siguiente intento...")
                time.sleep(sleep_time)
            else:
                logger.error("❌ Todos los intentos fallaron")
                
                # Último recurso: SQLite de emergencia
                if os.getenv("RAILWAY_ENVIRONMENT"):
                    logger.warning("🚨 Usando SQLite de emergencia en Railway")
                    return create_fallback_engine()
                else:
                    raise e

# Crear engine con reintentos
try:
    engine = create_engine_with_retry()
except Exception as e:
    logger.critical(f"🚨 Error crítico creando engine: {str(e)}")
    # Como último recurso, crear SQLite
    engine = create_fallback_engine()

# Session maker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Declarative base
Base = declarative_base()

# Dependencia de FastAPI mejorada
def get_db():
    """Dependencia mejorada con manejo de errores"""
    db = SessionLocal()
    try:
        # Test rápido de conexión
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        logger.error(f"❌ Error en sesión de BD: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

# Función para crear tablas con reintentos
def create_tables_safe():
    """Crear tablas de forma segura"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🔧 Creando tablas - intento {attempt + 1}")
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Tablas creadas exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando tablas (intento {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                logger.error("❌ No se pudieron crear las tablas")
                return False

# Función de diagnóstico
def diagnose_connection():
    """Diagnosticar problemas de conexión"""
    try:
        database_url = str(settings.database_url)
        logger.info(f"🔍 Diagnosticando conexión...")
        logger.info(f"📍 URL: {database_url[:50]}...")
        logger.info(f"🚂 Railway: {bool(os.getenv('RAILWAY_ENVIRONMENT'))}")
        
        # Variables de entorno relevantes
        env_vars = ["DATABASE_URL", "RAILWAY_ENVIRONMENT", "RAILWAY_PROJECT_ID"]
        for var in env_vars:
            value = os.getenv(var, "Not set")
            if "postgresql" in str(value).lower():
                logger.info(f"📍 {var}: {str(value)[:50]}...")
            else:
                logger.info(f"📍 {var}: {value}")
        
        # Test de conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1, current_database(), version()")).fetchone()
            logger.info(f"✅ Conexión exitosa - DB: {result[1]}")
            logger.info(f"📊 Versión: {result[2][:50]}...")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Diagnóstico falló: {str(e)}")
        return False

# Auto-inicialización en Railway
if os.getenv("RAILWAY_ENVIRONMENT"):
    logger.info("🚂 Detectado Railway - Inicializando...")
    
    # Diagnóstico
    connection_ok = diagnose_connection()
    
    if connection_ok:
        # Crear tablas
        tables_ok = create_tables_safe()
        
        if tables_ok:
            logger.info("🎉 Inicialización completa exitosa")
        else:
            logger.warning("⚠️ Tablas no se crearon correctamente")
    else:
        logger.error("🚨 Problemas de conexión detectados")

# Función de salud para endpoints
def get_db_health():
    """Verificar salud de la base de datos"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            return {
                "status": "✅ Healthy",
                "test_query": result[0],
                "engine_url": str(engine.url)[:50] + "..."
            }
    except Exception as e:
        return {
            "status": f"❌ Error: {str(e)}",
            "engine_url": str(engine.url)[:50] + "..."
        }