'''
    Configuración de la aplicación FastAPI utilizando Pydantic para la gestión de variables de entorno.
    Define las configuraciones necesarias para la aplicación, incluyendo la base de datos, el correo electrónico y la seguridad.
'''

# Librerías de terceros
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, AnyUrl, EmailStr, AnyHttpUrl

class Settings(BaseSettings):
    # App
    app_name: str
    debug: bool
    database_url: AnyUrl
    secret_key: str
    algorithm: str

    email_token_expiracion_minutos: int
    jwt_token_acceso_minutos: int

    cookie_access_token_name: str

    app_base_url: AnyHttpUrl

    email_host: str           
    email_port: int           
    email_use_tls: bool       
    email_host_user: EmailStr 
    email_host_password: str  
    mail_from_name: str      
    mail_template_folder: str

    redis_host: str 
    redis_port: int
    redis_db: int

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    timezone: str = "America/Bogota"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

settings = Settings()
