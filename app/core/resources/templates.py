'''
    Configuración global de Jinja2 para FastAPI.
'''

# Librerías de terceros
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/core/resources/templates")
