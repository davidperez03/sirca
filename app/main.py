'''
    Punto de entrada para la aplicación FastAPI.
    Configura la app, monta archivos estáticos, crea las tablas de la base de datos e incluye los routers de los módulos.
'''
# Importaciones de terceros
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


import os
import sqlite3
from datetime import datetime
from pathlib import Path
from sqlalchemy import text
import traceback


# Configuración principal
from app.core.config import settings
from app.core.dependencias.dependencias import engine, Base

# Routers de la aplicación
from app.modules.autenticacion.interface.rutas import router as usuarios_router
from app.modules.pertenencias.interface.rutas import router as pertenencias_router
from app.modules.vehiculos.interface.rutas import router as vehiculos_router
from app.routes.pages import router as pages_router

from app.modules.qr_acceso.interface.rutas import router as qr_acceso_router

app = FastAPI(title=settings.app_name, debug=settings.debug)


Base.metadata.create_all(bind=engine)

# Configuración de plantillas
app.mount("/static", StaticFiles(directory="app/core/resources/static"), name="static")
app.mount("/media", StaticFiles(directory="app/core/resources/media"), name="media")

templates = Jinja2Templates(directory="app/core/resources/templates")

# Montar el router de usuarios
app.include_router(usuarios_router)

# Montar otros routers de módulos aquí
app.include_router(pertenencias_router)
app.include_router(vehiculos_router)
app.include_router(qr_acceso_router)
app.include_router(pages_router)



# Ruta raíz
@app.get("/", response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse("inicio.html", {"request": request})

@app.get("/health")
async def health_check():
    """Endpoint básico de salud"""
    return {
        "status": "✅ API funcionando",
        "timestamp": datetime.now().isoformat(),
        "environment": "Railway" if os.getenv("RAILWAY_ENVIRONMENT") else "Local"
    }