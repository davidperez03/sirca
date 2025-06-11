from pydantic_settings import BaseSettings
from pydantic import ConfigDict, AnyUrl, EmailStr, AnyHttpUrl
import os

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
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""  
    redis_url: str = ""       

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    timezone: str = "America/Bogota"

    def get_redis_config(self) -> dict:
        if self.redis_url:
            return {"url": self.redis_url}
        
        config = {
            "host": self.redis_host,
            "port": self.redis_port,
            "db": self.redis_db,
            "decode_responses": True
        }

        if self.redis_password:
            config["password"] = self.redis_password
            
        return config

settings = Settings()