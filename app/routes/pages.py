"""
Rutas para páginas estáticas como About y Contact
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.dependencias.dependencias import get_db
from app.core.resources.templates import templates
from app.core.utils.contexto_usuario import obtener_contexto_usuario

logger = logging.getLogger(__name__)

router = APIRouter(tags=["pages"])

@router.get("/about", response_class=HTMLResponse, name="Acerca de")
async def about_page(request: Request, db: Session = Depends(get_db)):
    """Página Acerca de SIRCA"""
    context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse(
        "about.html",
        {
            "request": request,
            "title": "Acerca de SIRCA",
            **context
        }
    )

@router.get("/contact", response_class=HTMLResponse, name="Contacto")
async def contact_page(request: Request, db: Session = Depends(get_db)):
    """Página de contacto"""
    context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse(
        "contact.html",
        {
            "request": request,
            "title": "Contacto - SIRCA",
            "form_data": {},
            "mensaje": None,
            "error": None,
            **context
        }
    )

@router.post("/contact", response_class=HTMLResponse, name="Enviar contacto")
async def contact_submit(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(None),
    empresa: str = Form(None),
    asunto: str = Form(...),
    mensaje: str = Form(...),
    acepto: bool = Form(...),
    db: Session = Depends(get_db)
):
    """Procesar formulario de contacto"""
    context = obtener_contexto_usuario(request, db)
    
    # Datos del formulario para repoblar en caso de error
    form_data = {
        "nombre": nombre,
        "email": email,
        "telefono": telefono,
        "empresa": empresa,
        "asunto": asunto,
        "mensaje": mensaje
    }
    
    try:
        # Validaciones básicas
        if not acepto:
            raise ValueError("Debe aceptar los términos y condiciones")
        
        if len(nombre.strip()) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
            
        if len(mensaje.strip()) < 10:
            raise ValueError("El mensaje debe tener al menos 10 caracteres")
        
        # Aquí se podría enviar el email, guardar en BD, etc.
        # Por ahora solo simulamos el envío
        logger.info(f"📧 Mensaje de contacto recibido de {nombre} ({email})")
        logger.info(f"   Asunto: {asunto}")
        logger.info(f"   Empresa: {empresa or 'No especificada'}")
        logger.info(f"   Teléfono: {telefono or 'No especificado'}")
        logger.info(f"   Mensaje: {mensaje[:100]}...")
        
        # TODO: Aquí implementar:
        # 1. Envío de email al equipo de SIRCA
        # 2. Guardar en base de datos para seguimiento
        # 3. Envío de email de confirmación al usuario
        
        return templates.TemplateResponse(
            "contact.html",
            {
                "request": request,
                "title": "Contacto - SIRCA",
                "form_data": {},  # Limpiar formulario después del éxito
                "mensaje": "¡Gracias por contactarnos! Hemos recibido tu mensaje y te responderemos pronto.",
                "error": None,
                **context
            },
            status_code=status.HTTP_200_OK
        )
        
    except ValueError as e:
        logger.warning(f"⚠️ Error en formulario de contacto: {e}")
        return templates.TemplateResponse(
            "contact.html",
            {
                "request": request,
                "title": "Contacto - SIRCA",
                "form_data": form_data,
                "mensaje": None,
                "error": str(e),
                **context
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"❌ Error procesando contacto: {e}")
        return templates.TemplateResponse(
            "contact.html",
            {
                "request": request,
                "title": "Contacto - SIRCA", 
                "form_data": form_data,
                "mensaje": None,
                "error": "Ocurrió un error al enviar tu mensaje. Por favor, inténtalo de nuevo.",
                **context
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/privacy", response_class=HTMLResponse, name="Política de Privacidad")
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

@router.get("/terms", response_class=HTMLResponse, name="Términos de Uso")  
async def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@router.get("/help", response_class=HTMLResponse, name="Centro de Ayuda")
async def help_center(request: Request):
    return templates.TemplateResponse("help.html", {"request": request})