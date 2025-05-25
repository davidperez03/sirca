'''
    Modulo para enviar correos de restablecimiento de contrasena.
'''

# Biblioteca estándar
from datetime import datetime, timezone

# Librerías de terceros
from fastapi_mail import FastMail, MessageSchema

# Configuración principal
from app.core.config import settings

# Servicios de autenticación
from app.modules.auth.seguridad import crear_token_reset

# Configuración de email
from app.modules.autenticacion.infrastructure.email.config import conf

async def enviar_correo_reset(
    email_to: str,
    numero_documento: str,
    nombre_usuario: str
) -> None:
    # 1) Genera el JWT de reset
    token = crear_token_reset(numero_documento)

    # 2) Construye el enlace de restablecimiento
    base = str(settings.app_base_url).rstrip('/')
    reset_link = f"{base}/usuarios/reset-contrasena?token={token}"

    # 3) Data para la plantilla
    data = {
        "link": reset_link,
        "nombre_usuario": nombre_usuario,
        "email_token_expiracion_minutos": settings.email_token_expiracion_minutos,
        "año_actual": datetime.now(timezone.utc).year
    }

    # 4) Crea y envía el mensaje
    message = MessageSchema(
        subject="Recuperar contraseña",
        recipients=[email_to],
        template_body=data,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(
        message,
        template_name="resetear_contrasena.html" 
    )
