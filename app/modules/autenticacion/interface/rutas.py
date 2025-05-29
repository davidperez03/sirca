'''
    Define las rutas de FastAPI para la gestión de usuarios:
    - Registro
    - Activación y reenvío de activación
    - Login y logout
    - Recuperación y reseteo de contraseña
'''

from datetime import datetime

# FastAPI & terceros
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Form,
    BackgroundTasks,
    Query,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session
from jose import jwt, JWTError

# Configuración core
from app.core.config import settings
from app.core.dependencias.dependencias import get_db
from app.core.resources.templates import templates

# Dominio
from app.modules.autenticacion.domain.objetos_de_valor.enums.tipo_documento import TipoDocumento
from app.modules.autenticacion.domain.objetos_de_valor.enums.rol_usuario import RolUsuario
from app.modules.autenticacion.domain.constantes.rol_registro import ROLES_PERMITIDOS_REGISTRO

# Infraestructura
from app.modules.autenticacion.infrastructure.repositorios.repositorio import RepositorioUsuariosBD

# Casos de uso 
from app.modules.autenticacion.application.casos_de_uso.registrar_usuario import registrar_usuario
from app.modules.autenticacion.application.casos_de_uso.obtener_usuario import obtener_usuario
from app.modules.autenticacion.application.casos_de_uso.resetear_contrasena import resetear_contrasena

# Servicios
from app.modules.auth.servicios import ServicioAuth, verificar_token_reset
from app.modules.auth.blacklist import agregar_token_a_blacklist
from app.modules.auth.seguridad import decodificar_token
from app.modules.auth.blacklist import esta_en_blacklist

# Autenticación
from app.modules.auth.validadores.token_cookie import validar_token_cookie
from app.modules.auth.validadores.roles import rol_requerido_cookie

# Esquemas de entrada / salida
from app.modules.autenticacion.interface.esquemas import UsuarioRead

router = APIRouter(tags=["autenticacion"])
auth_service = ServicioAuth()

@router.get(
    "/registrarse", response_class=HTMLResponse,
    name="Mostrar formulario de registro"
)
async def mostrar_formulario(request: Request):
    return templates.TemplateResponse(
        "autenticacion/registro/registro.html",
        {
            "request": request,
            "tipos_documento": list(TipoDocumento),
            "roles": ROLES_PERMITIDOS_REGISTRO,
            "form_data": {}
        }
    )

@router.post(
    "/registrarse", response_class=HTMLResponse,
    status_code=status.HTTP_201_CREATED,
    name="Registrar usuario"
)
async def crear_usuario(
    request: Request,
    background_tasks: BackgroundTasks,
    tipo_documento: TipoDocumento = Form(...),
    numero_documento: str = Form(...),
    nombres: str = Form(...),
    apellidos: str = Form(...),
    correo_institucional: str = Form(...),
    contrasena: str = Form(...),
    confirmar_contrasena: str = Form(...),
    rol: RolUsuario = Form(...),
    db: Session = Depends(get_db)
):
    # 1) Validación cliente de contraseñas
    if contrasena != confirmar_contrasena:
        return templates.TemplateResponse(
            "autenticacion/registro/registro.html",
            {
                "request": request,
                "tipos_documento": list(TipoDocumento),
                "error": "Las contraseñas no coinciden.",
                "form_data": {
                    "tipo_documento": tipo_documento.name,
                    "numero_documento": numero_documento,
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "correo_institucional": correo_institucional,
                    "rol": rol.value
                }
            }
        )

    repo = RepositorioUsuariosBD(db)
    
    try:
        usuario = registrar_usuario(
            repo,
            tipo_documento,
            numero_documento,
            nombres,
            apellidos,
            correo_institucional,
            contrasena,
            rol
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "autenticacion/registro/registro.html",
            {
                "request": request,
                "tipos_documento": list(TipoDocumento),
                "roles": ROLES_PERMITIDOS_REGISTRO,
                "error": str(e),
                "form_data": {
                    "tipo_documento": tipo_documento.name,
                    "numero_documento": numero_documento,
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "correo_institucional": correo_institucional,
                    "rol": rol.value
                }
            }
        )

    # 3) Enviar correo de activación en background
    background_tasks.add_task(
        auth_service.enviar_activacion,
        numero_documento,
        f"{nombres} {apellidos}",
        correo_institucional
    )

    # 4) Mostrar éxito
    usuario_leido = UsuarioRead.from_domain(usuario)
    return templates.TemplateResponse(
        "autenticacion/registro/registro_exitoso.html",
        {"request": request, "usuario": usuario_leido}
    )

@router.get(
    "/activar", response_class=HTMLResponse,
    name="Activar cuenta"
)
def activar_cuenta(
    request: Request,
    token: str = Query(..., description="Token JWT de activación"),
    db: Session = Depends(get_db)
):
    if esta_en_blacklist(token):
        return templates.TemplateResponse(
            "autenticacion/activacion_usuario/activacion_error.html",
            {"request": request, "mensaje": "Este enlace ya fue utilizado."},
            status_code=400
        )
    
    try:
        user_id = auth_service.activar_cuenta(token)
    except HTTPException as e:
        return templates.TemplateResponse(
            "autenticacion/activacion_usuario/activacion_error.html",
            {"request": request, "mensaje": e.detail},
            status_code=e.status_code
        )

    # 2) Mostrar página de éxito
    repo = RepositorioUsuariosBD(db)
    usuario = repo.obtener_por_id(user_id)

    decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    exp = decoded.get("exp")
    tiempo_restante = exp - int(datetime.utcnow().timestamp())
    if tiempo_restante > 0:
        agregar_token_a_blacklist(token, tiempo_restante)

    return templates.TemplateResponse(
        "autenticacion/activacion_usuario/activacion_exitosa.html",
        {"request": request, "usuario": usuario}
    )


@router.get(
    "/reenvio-activacion",
    response_class=HTMLResponse,
    name="Reenviar activacion"
)
async def mostrar_reenvio_activacion(request: Request):
    return templates.TemplateResponse(
        "autenticacion/activacion_usuario/reenvio_activacion.html",
        {
            "request": request,
            "tipos_documento": list(TipoDocumento),
            "form_data": {},
            "error": None
        }
    )

@router.post(
    "/reenvio-activacion",
    response_class=HTMLResponse,
    name="Procesar reenvio activacion"
)
async def procesar_reenvio_activacion(
    request: Request,
    background_tasks: BackgroundTasks,
    tipo_documento: TipoDocumento = Form(...),
    numero_documento: str         = Form(...),
    db: Session                   = Depends(get_db)
):
    repo    = RepositorioUsuariosBD(db)
    usuario = repo.obtener_por_id(numero_documento)

    # 1) Usuario no encontrado o tipo incorrecto
    if not usuario or usuario.tipo_documento != tipo_documento:
        return templates.TemplateResponse(
            "autenticacion/activacion_usuario/reenvio_activacion.html",
            {
                "request": request,
                "tipos_documento": list(TipoDocumento),
                "form_data": {
                    "tipo_documento": tipo_documento.name,
                    "numero_documento": numero_documento
                },
                "error": "Usuario no encontrado."
            },
            status_code=status.HTTP_404_NOT_FOUND
        )

    # 2) Cuenta ya activada
    if usuario.activo:
        return templates.TemplateResponse(
            "autenticacion/activacion_usuario/reenvio_activacion.html",
            {
                "request": request,
                "tipos_documento": list(TipoDocumento),
                "form_data": {
                    "tipo_documento": tipo_documento.name,
                    "numero_documento": numero_documento
                },
                "error": "La cuenta ya está activada."
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 3) Envío exitoso
    background_tasks.add_task(
        auth_service.enviar_activacion,
        numero_documento=usuario.numero_documento.valor,
        nombre_usuario=f"{usuario.nombres.valor} {usuario.apellidos.valor}",
        email=usuario.correo_institucional.valor
    )
    return templates.TemplateResponse(
        "autenticacion/activacion_usuario/reenvio_exitoso.html",
        {"request": request}
    )

@router.get(
    "/login",
    response_class=HTMLResponse,
    name="Mostrar formulario de login"
)
async def mostrar_login(request: Request):
    return templates.TemplateResponse(
        "autenticacion/login/login.html",
        {
            "request": request,
            "tipos_documento": list(TipoDocumento),
            "form_data": {},
            "error": None
        }
    )

@router.post("/login", response_class=HTMLResponse, name="Iniciar sesión")

async def login(
    request: Request,
    tipo_documento: TipoDocumento = Form(...),
    numero_documento: str = Form(...),
    contrasena: str = Form(...),
    db: Session = Depends(get_db)
):
    form_data = {"tipo_documento": tipo_documento.name, "numero_documento": numero_documento}

    try:
        token = auth_service.login(tipo_documento, numero_documento, contrasena)
    except HTTPException as e:
        return templates.TemplateResponse(
            "autenticacion/login/login.html",
            {
                "request": request,
                "tipos_documento": list(TipoDocumento),
                "form_data": form_data,
                "error": e.detail,
            },
            status_code=e.status_code,
        )

    response = RedirectResponse(url="/perfil", status_code=303)

    response.set_cookie(
        key=settings.cookie_access_token_name,
        value=token,
        httponly=True,     # Seguridad extra
        samesite="lax",    # Para proteger CSRF
        secure=False       # En producción, True si usas HTTPS
    )
    return response

@router.get("/perfil", response_class=HTMLResponse, name="Perfil de usuario")
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz")
async def ver_perfil(
    request: Request,
    usuario_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo = RepositorioUsuariosBD(db)
    usuario = repo.obtener_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario_leido = UsuarioRead.from_domain(usuario)
    
    return templates.TemplateResponse(
        "dashboard_usuario/perfil/perfil.html",
        {
            "request": request,
            "usuario": usuario_leido,
            "usuario_autenticado": True,
            "usuario_nombre": f"{usuario_leido.nombres} {usuario_leido.apellidos}"
        }
    )

@router.get(
    "/logout",
    response_class=HTMLResponse,
    name="Cerrar sesión"
)
async def logout(request: Request, response: Response):
    token = request.cookies.get("access_token")

    if token:
        try:
            payload = decodificar_token(token)
            exp = payload.get("exp")
            if exp:
                tiempo_restante = exp - int(datetime.utcnow().timestamp())
                if tiempo_restante > 0:
                    agregar_token_a_blacklist(token, tiempo_restante)
        except JWTError:
            pass

        response = templates.TemplateResponse(
            "autenticacion/logout/logout_exitoso.html",
            {"request": request}
        )
        response.delete_cookie("access_token")
        return response

    # Si no había token, igual mostramos logout exitoso
    return templates.TemplateResponse(
        "autenticacion/logout/logout_exitoso.html",
        {"request": request}
    )

@router.get(
    "/recuperar-contrasena",
    response_class=HTMLResponse,
    name="Mostrar recuperar contraseña"
)

async def mostrar_recuperar_contrasena(request: Request):
    return templates.TemplateResponse(
        "autenticacion/recuperar_contrasena/recuperar_contrasena.html",
        {
            "request": request,
            "tipos_documento": list(TipoDocumento),
            "form_data": {},
            "error": None
        }
    )

@router.post(
    "/recuperar-contrasena",
    response_class=HTMLResponse,
    name="Procesar recuperar contraseña"
)

async def procesar_recuperar(
    request: Request,
    background_tasks: BackgroundTasks,
    tipo_documento: TipoDocumento = Form(...),
    numero_documento: str         = Form(...),
    correo: str                   = Form(...),
    db: Session                   = Depends(get_db)
):
    repo    = RepositorioUsuariosBD(db)
    usuario = repo.obtener_por_correo(correo)

    ctx = {
        "request": request,
        "tipos_documento": list(TipoDocumento),
        "form_data": {
            "tipo_documento": tipo_documento.name,
            "numero_documento": numero_documento,
            "correo": correo
        },
        "error": None
    }

    if (not usuario
        or usuario.tipo_documento != tipo_documento
        or usuario.numero_documento.valor != numero_documento):
        ctx["error"] = "Los datos no coinciden con ningún usuario."
        return templates.TemplateResponse(
            "autenticacion/recuperar_contrasena/recuperar_contrasena.html", ctx
        )

    # disparar el correo de reset
    background_tasks.add_task(
        auth_service.enviar_reset_contrasena,
        numero_documento=usuario.numero_documento.valor,
        nombre_usuario=f"{usuario.nombres.valor} {usuario.apellidos.valor}",
        email=usuario.correo_institucional.valor
    )
    return templates.TemplateResponse(
        "autenticacion/recuperar_contrasena/recuperar_exitoso.html",
        {"request": request}
    )

# 3. Mostrar formulario para nueva contraseña
@router.get(
    "/reset-contrasena",
    response_class=HTMLResponse,
    name="Mostrar reset contraseña"
)
async def mostrar_reset(request: Request, token: str = Query(...)):
    return templates.TemplateResponse(
        "autenticacion/recuperar_contrasena/reset_contrasena.html",
        {"request": request, "token": token, "error": None}
    )

# 4. Procesar el cambio de contraseña
@router.post(
    "/reset-contrasena",
    response_class=HTMLResponse,
    name="Procesar reset contraseña"
)
async def procesar_reset(
    request: Request,
    token: str               = Form(...),
    nueva_contrasena: str    = Form(...),
    confirmar_contrasena: str= Form(...),
    db: Session              = Depends(get_db)
):
    if nueva_contrasena != confirmar_contrasena:
        return templates.TemplateResponse(
            "autenticacion/recuperar_contrasena/reset_contrasena.html",
            {"request": request, "token": token, "error": "Las contraseñas no coinciden."}
        )
    
    if esta_en_blacklist(token):
        return templates.TemplateResponse(
            "autenticacion/recuperar_contrasena/reset_error.html",
            {"request": request, "mensaje": "Este enlace ya fue utilizado o ha expirado."}
    )

    try:
        user_id = verificar_token_reset(token)
    except ValueError as e:
        return templates.TemplateResponse(
            "autenticacion/recuperar_contrasena/reset_error.html",
            {"request": request, "mensaje": str(e)}
        )

    repo = RepositorioUsuariosBD(db)
    usuario = repo.obtener_por_id(user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    try:
        resetear_contrasena(usuario, nueva_contrasena)
    except ValueError as e:
        return templates.TemplateResponse(
            "autenticacion/recuperar_contrasena/reset_contrasena.html",
            {"request": request, "token": token, "error": str(e)}
        )

    repo.actualizar(usuario)

    decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    exp = decoded.get("exp")
    tiempo_restante = exp - int(datetime.utcnow().timestamp())
    if tiempo_restante > 0:
        agregar_token_a_blacklist(token, tiempo_restante)

    return templates.TemplateResponse(
        "autenticacion/recuperar_contrasena/reset_exitoso.html",
        {"request": request}
    )

@router.get(
    "/{tipo_doc}/{numero_doc}", response_class=HTMLResponse,
    name="Ver usuario"
)
async def ver_usuario(
    request: Request,
    tipo_doc: TipoDocumento,
    numero_doc: str,
    db: Session = Depends(get_db)
):
    repo = RepositorioUsuariosBD(db)
    usuario = obtener_usuario(repo, tipo_doc, numero_doc)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario_leido = UsuarioRead.from_domain(usuario)
    return templates.TemplateResponse(
        "autenticacion/usuario_detalle.html",
        {"request": request, "usuario": usuario_leido}
    )
