'''
    Envío de correos electrónicos para la activación de cuentas.
    Este módulo se encarga de enviar correos electrónicos a los usuarios para activar sus cuentas después de registrarse.
'''

# Biblioteca estándar
from datetime import datetime, timezone

# Librerías de terceros
from fastapi_mail import FastMail, MessageSchema

# Configuración de email
from app.modules.autenticacion.infrastructure.email.config import conf

# Configuración principal
from app.core.config import settings

# Servicios de autenticación
from app.modules.auth.seguridad import crear_token_activacion

async def enviar_correo_activacion(
    email_to: str,
    numero_documento: str,
    nombre_usuario: str
) -> None:
    # 1) Genera el JWT de activación
    token = crear_token_activacion(numero_documento)

    # 2) Construye el enlace de activación
    base = str(settings.app_base_url).rstrip('/')
    activation_link = f"{base}/activar?token={token}"

    # 3) Data para la plantilla
    data = {
        "link": activation_link,
        "nombre_usuario": nombre_usuario,
        "año_actual": datetime.now(timezone.utc).year
    }

    # 4) Crea y envía el mensaje
    message = MessageSchema(
        subject="Activa tu cuenta",
        recipients=[email_to],
        template_body=data,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(
        message,
        template_name="activar.html"
    )


