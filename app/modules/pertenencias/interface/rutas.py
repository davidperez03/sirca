from fastapi import (
    APIRouter,
    Request,
    Depends,
    Form,
    File,
    UploadFile,
    Query,
    status,
    HTTPException,
)
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List

from app.modules.pertenencias.infrastructure.repositorios.repositorio import RepositorioPertenenciasBD
from app.modules.autenticacion.infrastructure.repositorios.repositorio import RepositorioUsuariosBD
from app.modules.pertenencias.application.casos_de_uso.registrar_pertenencia import RegistrarPertenencia
from app.modules.pertenencias.application.casos_de_uso.listar_pertenencias_usuario import ListarPertenenciasUsuario
from app.modules.pertenencias.application.casos_de_uso.obtener_pertenencia import ObtenerPertenencia
from app.modules.pertenencias.application.casos_de_uso.actualizar_pertenencia import ActualizarPertenencia
from app.modules.pertenencias.application.casos_de_uso.eliminar_pertenencia import EliminarPertenencia

from app.modules.pertenencias.interface.esquemas import (
    PertenenciaRead, PertenenciaResumen, EstadisticasPertenencias, 
    TipoPertenenciaInfo
)
from app.modules.pertenencias.domain.objetos_de_valor.tipo_pertenencia import TipoPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.estado_pertenencia import EstadoPertenencia

from app.core.resources.templates import templates
from app.core.dependencias.dependencias import get_db
from app.core.utils.contexto_usuario import obtener_contexto_usuario

# Importar validación de token
from app.modules.auth.validadores.token_cookie import validar_token_cookie
from app.modules.auth.validadores.roles import rol_requerido_cookie

router = APIRouter(tags=["pertenencias"])

# ======================== RUTAS WEB (HTML) ========================

@router.get(
    "/usuario/{usuario_id}/pertenencias",
    response_class=HTMLResponse,
    name="Listar pertenencias de usuario"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def listar_pertenencias_usuario(
    request: Request, 
    usuario_id: str,
    buscar: Optional[str] = Query(None, description="Término de búsqueda"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (activo/inactivo)"),
    incluir_inactivos: bool = Query(False, description="Incluir pertenencias inactivas"),
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_pertenencias = RepositorioPertenenciasBD(db, repo_usuarios)
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Determinar si incluir inactivos
    mostrar_inactivos = incluir_inactivos or estado == "inactivo"
    
    # Obtener pertenencias según filtros
    if buscar:
        pertenencias = repo_pertenencias.buscar_por_nombre(buscar, usuario_id, mostrar_inactivos)
    elif tipo:
        pertenencias = repo_pertenencias.listar_por_tipo(tipo, mostrar_inactivos)
        pertenencias = [p for p in pertenencias if p.usuario.numero_documento.valor == usuario_id]
    else:
        pertenencias = repo_pertenencias.listar_por_usuario(usuario_id, mostrar_inactivos)
    
    # Filtrar por estado específico si se solicita
    if estado == "activo":
        pertenencias = [p for p in pertenencias if p.estado.value == "Activo"]
    elif estado == "inactivo":
        pertenencias = [p for p in pertenencias if p.estado.value == "Inactivo"]
    
    # Obtener estadísticas
    estadisticas = repo_pertenencias.contar_por_usuario(usuario_id)
    
    # Obtener contexto de usuario autenticado
    user_context = obtener_contexto_usuario(request, db)

    return templates.TemplateResponse(
        "pertenencias/listar.html",
        {
            "request": request, 
            "usuario": usuario, 
            "pertenencias": pertenencias,
            "estadisticas": estadisticas,
            "tipos_pertenencia": list(TipoPertenencia),
            "buscar": buscar,
            "tipo_filtro": tipo,
            "estado_filtro": estado,
            "mostrar_inactivas": incluir_inactivos,
            **user_context
        }
    )

@router.get(
    "/usuario/{usuario_id}/pertenencias/registrar",
    response_class=HTMLResponse,
    name="Mostrar formulario registrar pertenencia"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
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
    
    # Preparar información de tipos
    tipos_info = [TipoPertenenciaInfo.from_enum(tipo) for tipo in TipoPertenencia]
    
    user_context = obtener_contexto_usuario(request, db)

    return templates.TemplateResponse(
        "pertenencias/registrar.html",
        {
            "request": request, 
            "usuario": usuario, 
            "tipos_pertenencia": list(TipoPertenencia),
            "tipos_info": tipos_info,
            "estados": list(EstadoPertenencia),
            "form_data": {},
            **user_context
        }
    )

@router.post(
    "/usuario/{usuario_id}/pertenencias/registrar",
    response_class=HTMLResponse,
    name="Registrar pertenencia"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def registrar_pertenencia(
    request: Request,
    usuario_id: str,
    nombre: str = Form(...),
    tipo: str = Form(...),
    descripcion: str = Form(""),
    serial: str = Form(""),
    estado: str = Form("Activo"),
    foto: Optional[UploadFile] = File(None),
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_pertenencias = RepositorioPertenenciasBD(db, repo_usuarios)
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    
    user_context = obtener_contexto_usuario(request, db)
    tipos_info = [TipoPertenenciaInfo.from_enum(t) for t in TipoPertenencia]

    if not usuario:
        return templates.TemplateResponse(
            "pertenencias/registrar.html",
            {
                "request": request, 
                "usuario": None, 
                "error": "Usuario no encontrado", 
                "tipos_pertenencia": list(TipoPertenencia),
                "tipos_info": tipos_info,
                "estados": list(EstadoPertenencia),
                "form_data": {},
                **user_context
            },
            status_code=404
        )
    
    caso_uso = RegistrarPertenencia(repo_pertenencias)
    try:
        await caso_uso.ejecutar(
            nombre=nombre,
            tipo=tipo,
            descripcion=descripcion,
            serial=serial,
            usuario=usuario,
            estado=estado,
            archivo_foto=foto
        )
        
    except ValueError as e:
        return templates.TemplateResponse(
            "pertenencias/registrar.html",
            {
                "request": request,
                "usuario": usuario,
                "error": str(e),
                "tipos_pertenencia": list(TipoPertenencia),
                "tipos_info": tipos_info,
                "estados": list(EstadoPertenencia),
                "form_data": {
                    "nombre": nombre,
                    "tipo": tipo,
                    "descripcion": descripcion,
                    "serial": serial,
                    "estado": estado
                },
                **user_context
            }
        )
    
    return RedirectResponse(
        url=f"/usuario/{usuario_id}/pertenencias",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get(
    "/usuario/{usuario_id}/pertenencias/{pertenencia_id:int}",
    response_class=HTMLResponse,
    name="Ver detalle pertenencia"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def ver_detalle_pertenencia(
    request: Request,
    usuario_id: str,
    pertenencia_id: int,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_pertenencias = RepositorioPertenenciasBD(db, repo_usuarios)
    
    caso_uso = ObtenerPertenencia(repo_pertenencias)
    pertenencia = caso_uso.ejecutar(pertenencia_id)
    
    if not pertenencia:
        raise HTTPException(status_code=404, detail="Pertenencia no encontrada")
    
    # Verificar que pertenece al usuario solicitado
    if pertenencia.usuario.numero_documento.valor != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse(
        "pertenencias/detalle.html",
        {
            "request": request,
            "pertenencia": pertenencia,
            "usuario": pertenencia.usuario,
            **user_context
        }
    )

@router.get(
    "/usuario/{usuario_id}/pertenencias/{pertenencia_id:int}/editar",
    response_class=HTMLResponse,
    name="Mostrar formulario editar pertenencia"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def mostrar_formulario_editar_pertenencia(
    request: Request,
    usuario_id: str,
    pertenencia_id: int,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_pertenencias = RepositorioPertenenciasBD(db, repo_usuarios)
    
    caso_uso = ObtenerPertenencia(repo_pertenencias)
    pertenencia = caso_uso.ejecutar(pertenencia_id)
    
    if not pertenencia:
        raise HTTPException(status_code=404, detail="Pertenencia no encontrada")
    
    # Verificar permisos
    if pertenencia.usuario.numero_documento.valor != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    tipos_info = [TipoPertenenciaInfo.from_enum(tipo) for tipo in TipoPertenencia]
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse(
        "pertenencias/editar.html",
        {
            "request": request,
            "pertenencia": pertenencia,
            "usuario": pertenencia.usuario,
            "tipos_pertenencia": list(TipoPertenencia),
            "tipos_info": tipos_info,
            "estados": list(EstadoPertenencia),
            **user_context
        }
    )

@router.post(
    "/usuario/{usuario_id}/pertenencias/{pertenencia_id:int}/editar",
    response_class=HTMLResponse,
    name="Actualizar pertenencia"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def actualizar_pertenencia_route(
    request: Request,
    usuario_id: str,
    pertenencia_id: int,
    nombre: Optional[str] = Form(None),
    tipo: Optional[str] = Form(None),
    descripcion: Optional[str] = Form(None),
    nuevo_serial: Optional[str] = Form(None),
    estado: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    eliminar_foto: bool = Form(False),
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_pertenencias = RepositorioPertenenciasBD(db, repo_usuarios)
    
    # Verificar que la pertenencia existe y pertenece al usuario
    pertenencia_actual = repo_pertenencias.obtener_por_id(pertenencia_id)
    if not pertenencia_actual:
        raise HTTPException(status_code=404, detail="Pertenencia no encontrada")
    
    if pertenencia_actual.usuario.numero_documento.valor != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    caso_uso = ActualizarPertenencia(repo_pertenencias)
    try:
        await caso_uso.ejecutar(
            id_pertenencia=pertenencia_id,
            nombre=nombre,
            tipo=tipo,
            descripcion=descripcion,
            nuevo_serial=nuevo_serial,
            estado=estado,
            archivo_foto=foto,
            eliminar_foto=eliminar_foto
        )
    except ValueError as e:
        user_context = obtener_contexto_usuario(request, db)
        tipos_info = [TipoPertenenciaInfo.from_enum(t) for t in TipoPertenencia]
        
        return templates.TemplateResponse(
            "pertenencias/editar.html",
            {
                "request": request,
                "pertenencia": pertenencia_actual,
                "usuario": pertenencia_actual.usuario,
                "error": str(e),
                "tipos_pertenencia": list(TipoPertenencia),
                "tipos_info": tipos_info,
                "estados": list(EstadoPertenencia),
                **user_context
            }
        )
    
    return RedirectResponse(
        url=f"/usuario/{usuario_id}/pertenencias/{pertenencia_id}",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post(
    "/usuario/{usuario_id}/pertenencias/{pertenencia_id:int}/reactivar",
    response_class=HTMLResponse,
    name="Reactivar pertenencia"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def reactivar_pertenencia_route(
    request: Request,
    usuario_id: str,
    pertenencia_id: int,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_pertenencias = RepositorioPertenenciasBD(db, repo_usuarios)
    
    # Verificar que la pertenencia existe y pertenece al usuario
    pertenencia = repo_pertenencias.obtener_por_id(pertenencia_id)
    if not pertenencia:
        raise HTTPException(status_code=404, detail="Pertenencia no encontrada")
    
    if pertenencia.usuario.numero_documento.valor != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Reactivar (cambiar estado a Activo)
    caso_uso = ActualizarPertenencia(repo_pertenencias)
    try:
        caso_uso.ejecutar_sin_archivo(
            id_pertenencia=pertenencia_id,
            estado="Activo"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return RedirectResponse(
        url=f"/usuario/{usuario_id}/pertenencias?incluir_inactivos=true",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post(
    "/usuario/{usuario_id}/pertenencias/{pertenencia_id:int}/eliminar",
    response_class=HTMLResponse,
    name="Eliminar pertenencia"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def eliminar_pertenencia_route(
    request: Request,
    usuario_id: str,
    pertenencia_id: int,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_pertenencias = RepositorioPertenenciasBD(db, repo_usuarios)
    
    # Verificar si la pertenencia está activa para decidir si desactivar o eliminar
    pertenencia = repo_pertenencias.obtener_por_id(pertenencia_id)
    if not pertenencia:
        raise HTTPException(status_code=404, detail="Pertenencia no encontrada")
    
    if pertenencia.usuario.numero_documento.valor != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    if pertenencia.estado.value == "Activo":
        # Si está activa, solo desactivar (inactivar)
        caso_uso_actualizar = ActualizarPertenencia(repo_pertenencias)
        try:
            caso_uso_actualizar.ejecutar_sin_archivo(
                id_pertenencia=pertenencia_id,
                estado="Inactivo"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        return RedirectResponse(
            url=f"/usuario/{usuario_id}/pertenencias?incluir_inactivos=true",
            status_code=status.HTTP_303_SEE_OTHER
        )
    else:
        # Si ya está inactiva, eliminar permanentemente
        caso_uso = EliminarPertenencia(repo_pertenencias)
        try:
            caso_uso.ejecutar(pertenencia_id, usuario_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        return RedirectResponse(
            url=f"/usuario/{usuario_id}/pertenencias",
            status_code=status.HTTP_303_SEE_OTHER
        )

# ======================== RUTAS API (JSON) ========================

@router.get(
    "/api/usuario/{usuario_id}/pertenencias",
    response_model=List[PertenenciaResumen],
    name="API Listar pertenencias"
)
async def api_listar_pertenencias(
    usuario_id: str,
    buscar: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    incluir_inactivos: bool = Query(False),
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_pertenencias = RepositorioPertenenciasBD(db, repo_usuarios)
    
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if buscar:
        pertenencias = repo_pertenencias.buscar_por_nombre(buscar, usuario_id)
    elif tipo:
        pertenencias = repo_pertenencias.listar_por_tipo(tipo, incluir_inactivos)
        pertenencias = [p for p in pertenencias if p.usuario.numero_documento.valor == usuario_id]
    else:
        pertenencias = repo_pertenencias.listar_por_usuario(usuario_id, incluir_inactivos)
    
    return [PertenenciaResumen.from_domain(p) for p in pertenencias]

@router.get(
    "/api/usuario/{usuario_id}/pertenencias/{pertenencia_id:int}",
    response_model=PertenenciaRead,
    name="API Obtener pertenencia"
)
async def api_obtener_pertenencia(
    usuario_id: str,
    pertenencia_id: int,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_pertenencias = RepositorioPertenenciasBD(db, repo_usuarios)
    
    caso_uso = ObtenerPertenencia(repo_pertenencias)
    pertenencia = caso_uso.ejecutar(pertenencia_id)
    
    if not pertenencia:
        raise HTTPException(status_code=404, detail="Pertenencia no encontrada")
    
    if pertenencia.usuario.numero_documento.valor != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    return PertenenciaRead.from_domain(pertenencia)

@router.get(
    "/api/usuario/{usuario_id}/pertenencias/estadisticas",
    response_model=EstadisticasPertenencias,
    name="API Estadísticas pertenencias"
)
async def api_estadisticas_pertenencias(
    usuario_id: str,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_pertenencias = RepositorioPertenenciasBD(db, repo_usuarios)
    
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    estadisticas = repo_pertenencias.contar_por_usuario(usuario_id)
    return EstadisticasPertenencias(**estadisticas)

@router.get(
    "/api/tipos-pertenencia",
    response_model=List[TipoPertenenciaInfo],
    name="API Tipos de pertenencia"
)
async def api_tipos_pertenencia():
    return [TipoPertenenciaInfo.from_enum(tipo) for tipo in TipoPertenencia]

@router.post(
    "/api/usuario/{usuario_id}/pertenencias/{pertenencia_id:int}/subir-foto",
    name="API Subir foto"
)
async def api_subir_foto(
    usuario_id: str,
    pertenencia_id: int,
    foto: UploadFile = File(...),
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_pertenencias = RepositorioPertenenciasBD(db, repo_usuarios)
    
    # Verificar pertenencia por ID
    pertenencia = repo_pertenencias.obtener_por_id(pertenencia_id)
    if not pertenencia:
        raise HTTPException(status_code=404, detail="Pertenencia no encontrada")
    
    if pertenencia.usuario.numero_documento.valor != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Actualizar con nueva foto
    caso_uso = ActualizarPertenencia(repo_pertenencias)
    try:
        await caso_uso.ejecutar(
            id_pertenencia=pertenencia_id,
            archivo_foto=foto
        )
        
        # Obtener pertenencia actualizada para retornar URL
        pertenencia_actualizada = repo_pertenencias.obtener_por_id(pertenencia_id)
        return {
            "success": True,
            "foto_url": pertenencia_actualizada.foto.obtener_url_publica(),
            "message": "Foto subida correctamente"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))