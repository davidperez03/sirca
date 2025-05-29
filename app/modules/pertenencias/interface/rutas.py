from fastapi import (
    APIRouter,
    Request,
    Depends,
    Form,
    status,
    HTTPException,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.modules.pertenencias.infrastructure.repositorios.repositorio import RepositorioPertenenciasBD
from app.modules.autenticacion.infrastructure.repositorios.repositorio import RepositorioUsuariosBD
from app.modules.pertenencias.application.casos_de_uso.registrar_pertenencia import RegistrarPertenencia
from app.modules.pertenencias.application.casos_de_uso.listar_pertenencias_usuario import ListarPertenenciasUsuario
from app.modules.pertenencias.interface.esquemas import PertenenciaCreate
from app.core.resources.templates import templates
from app.core.dependencias.dependencias import get_db

from app.core.utils.contexto_usuario import obtener_contexto_usuario

# Importar validación de token
from app.modules.auth.validadores.token_cookie import validar_token_cookie
from app.modules.auth.validadores.roles import rol_requerido_cookie

router = APIRouter(tags=["pertenencias"])

@router.get(
    "/usuario/{usuario_id}/pertenencias",
    response_class=HTMLResponse,
    name="Listar pertenencias de usuario"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz")
async def listar_pertenencias_usuario(
    request: Request, 
    usuario_id: str, 
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_pertenencias = RepositorioPertenenciasBD(db, repo_usuarios)
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    caso_uso = ListarPertenenciasUsuario(repo_pertenencias)
    pertenencias = caso_uso.ejecutar(usuario)
    
    # Obtener contexto de usuario autenticado
    user_context = obtener_contexto_usuario(request, db)

    return templates.TemplateResponse(
        "pertenencias/listar.html",
        {
            "request": request, 
            "usuario": usuario, 
            "pertenencias": pertenencias,
            **user_context  # Agregar contexto de autenticación
        }
    )

@router.get(
    "/usuario/{usuario_id}/pertenencias/registrar",
    response_class=HTMLResponse,
    name="Mostrar formulario registrar pertenencia"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz")
async def mostrar_formulario_registrar_pertenencia(
    request: Request, 
    usuario_id: str, 
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Obtener contexto de usuario autenticado
    user_context = obtener_contexto_usuario(request, db)

    return templates.TemplateResponse(
        "pertenencias/registrar.html",
        {
            "request": request, 
            "usuario": usuario, 
            "form_data": {},
            **user_context  # Agregar contexto de autenticación
        }
    )

@router.post(
    "/usuario/{usuario_id}/pertenencias/registrar",
    response_class=HTMLResponse,
    name="Registrar pertenencia"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz")
async def registrar_pertenencia(
    request: Request,
    usuario_id: str,
    nombre: str = Form(...),
    tipo: str = Form(...),
    descripcion: str = Form(""),
    serial: str = Form(""),
    foto: str = Form(""),
    estado: str = Form("Activo"),
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_pertenencias = RepositorioPertenenciasBD(db, repo_usuarios)
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    
    # Obtener contexto de usuario autenticado
    user_context = obtener_contexto_usuario(request, db)

    if not usuario:
        return templates.TemplateResponse(
            "pertenencias/registrar.html",
            {
                "request": request, 
                "usuario": None, 
                "error": "Usuario no encontrado", 
                "form_data": {},
                **user_context
            },
            status_code=404
        )
    
    caso_uso = RegistrarPertenencia(repo_pertenencias)
    try:
        caso_uso.ejecutar(
            nombre=nombre,
            tipo=tipo,
            descripcion=descripcion,
            serial=serial,
            foto=foto,
            usuario=usuario,
            estado=estado
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "pertenencias/registrar.html",
            {
                "request": request,
                "usuario": usuario,
                "error": str(e),
                "form_data": {
                    "nombre": nombre,
                    "tipo": tipo,
                    "descripcion": descripcion,
                    "serial": serial,
                    "foto": foto,
                    "estado": estado
                },
                **user_context
            }
        )
    
    return RedirectResponse(
        url=f"/usuario/{usuario_id}/pertenencias",
        status_code=status.HTTP_303_SEE_OTHER
    )