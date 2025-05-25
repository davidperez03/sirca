'''
    configuración para el envío de correos electrónicos utilizando la libreria FastAPI Mail.
    Se utiliza para enviar correos electrónicos de verificación, restablecimiento de contraseña, etc.
    Se define la configuración del servidor de correo, las credenciales y la carpeta de plantillas.
'''
# Librerías de terceros
from fastapi_mail import ConnectionConfig

# Configuración principal
from app.core.config import settings


conf = ConnectionConfig(
    MAIL_USERNAME   = settings.email_host_user,
    MAIL_PASSWORD   = settings.email_host_password,
    MAIL_FROM       = f"{settings.mail_from_name} <{settings.email_host_user}>",
    MAIL_SERVER     = settings.email_host,
    MAIL_PORT       = settings.email_port,
    MAIL_STARTTLS   = settings.email_use_tls,
    MAIL_SSL_TLS    = False,
    TEMPLATE_FOLDER = settings.mail_template_folder,
    USE_CREDENTIALS = True,
    SUPPRESS_SEND   = False,
)
