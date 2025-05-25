'''
    Configuración de la aplicación FastAPI utilizando Pydantic para la gestión de variables de entorno.
    Define las configuraciones necesarias para la aplicación, incluyendo:

    - Base de datos (DATABASE_URL)
    - Seguridad de JWT (SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES)
    - Correo electrónico (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, MAIL_FROM)
    - Otros ajustes (DEBUG, VERSION, etc.)

    Cada atributo se obtiene directamente de las variables de entorno y garantiza tipado
    y validación automática.
'''

# Librerías de terceros
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Configuración principal
from app.core.config import settings


# Para SQLite necesitamos desactivar el mismo hilo en check_same_thread
engine = create_engine(
    str(settings.database_url),
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

# Crea la fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base para los modelos
Base = declarative_base()

# Dependencia de FastAPI para inyectar sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
