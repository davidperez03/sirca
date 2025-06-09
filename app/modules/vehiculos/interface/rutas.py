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

from app.modules.vehiculos.infrastructure.repositorios.repositorio import RepositorioVehiculosBD
from app.modules.autenticacion.infrastructure.repositorios.repositorio import RepositorioUsuariosBD
from app.modules.vehiculos.application.casos_de_uso.registrar_vehiculo import RegistrarVehiculo
from app.modules.vehiculos.application.casos_de_uso.listar_vehiculos_usuario import ListarVehiculosUsuario
from app.modules.vehiculos.application.casos_de_uso.obtener_vehiculo import ObtenerVehiculo
from app.modules.vehiculos.application.casos_de_uso.actualizar_vehiculo import ActualizarVehiculo
from app.modules.vehiculos.application.casos_de_uso.eliminar_vehiculo import EliminarVehiculo

from app.modules.vehiculos.interface.esquemas import (
    VehiculoRead, VehiculoResumen, EstadisticasVehiculos, 
    TipoVehiculoInfo
)
from app.modules.vehiculos.domain.objetos_de_valor.tipo_vehiculo import TipoVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.estado_vehiculo import EstadoVehiculo

from app.core.resources.templates import templates
from app.core.dependencias.dependencias import get_db
from app.core.utils.contexto_usuario import obtener_contexto_usuario

# Importar validación de token
from app.modules.auth.validadores.token_cookie import validar_token_cookie
from app.modules.auth.validadores.roles import rol_requerido_cookie

router = APIRouter(tags=["vehiculos"])

# ======================== RUTAS WEB (HTML) ========================

@router.get(
    "/usuario/{usuario_id}/vehiculos",
    response_class=HTMLResponse,
    name="Listar vehiculos de usuario"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def listar_vehiculos_usuario(
    request: Request, 
    usuario_id: str,
    buscar: Optional[str] = Query(None, description="Término de búsqueda"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (activo/inactivo)"),
    incluir_inactivos: bool = Query(False, description="Incluir vehículos inactivos"),
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_vehiculos = RepositorioVehiculosBD(db, repo_usuarios)
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Determinar si incluir inactivos
    mostrar_inactivos = incluir_inactivos or estado == "inactivo"
    
    # Obtener vehículos según filtros
    if buscar:
        vehiculos = repo_vehiculos.buscar_por_marca_modelo(buscar, usuario_id, mostrar_inactivos)
    elif tipo:
        vehiculos = repo_vehiculos.listar_por_tipo(tipo, mostrar_inactivos)
        vehiculos = [v for v in vehiculos if v.usuario.numero_documento.valor == usuario_id]
    else:
        vehiculos = repo_vehiculos.listar_por_usuario(usuario_id, mostrar_inactivos)
    
    # Filtrar por estado específico si se solicita
    if estado == "activo":
        vehiculos = [v for v in vehiculos if v.estado.value == "Activo"]
    elif estado == "inactivo":
        vehiculos = [v for v in vehiculos if v.estado.value == "Inactivo"]
    
    # Obtener estadísticas
    estadisticas = repo_vehiculos.contar_por_usuario(usuario_id)
    
    # Obtener contexto de usuario autenticado
    user_context = obtener_contexto_usuario(request, db)

    return templates.TemplateResponse(
        "vehiculos/listar.html",
        {
            "request": request, 
            "usuario": usuario, 
            "vehiculos": vehiculos,
            "estadisticas": estadisticas,
            "tipos_vehiculo": list(TipoVehiculo),
            "buscar": buscar,
            "tipo_filtro": tipo,
            "estado_filtro": estado,
            "mostrar_inactivos": incluir_inactivos,
            **user_context
        }
    )

@router.get(
    "/usuario/{usuario_id}/vehiculos/registrar",
    response_class=HTMLResponse,
    name="Mostrar formulario registrar vehiculo"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def mostrar_formulario_registrar_vehiculo(
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
    tipos_info = [TipoVehiculoInfo.from_enum(tipo) for tipo in TipoVehiculo]
    
    user_context = obtener_contexto_usuario(request, db)

    return templates.TemplateResponse(
        "vehiculos/registrar.html",
        {
            "request": request, 
            "usuario": usuario, 
            "tipos_vehiculo": list(TipoVehiculo),
            "tipos_info": tipos_info,
            "estados": list(EstadoVehiculo),
            "form_data": {},
            **user_context
        }
    )

@router.post(
    "/usuario/{usuario_id}/vehiculos/registrar",
    response_class=HTMLResponse,
    name="Registrar vehiculo"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def registrar_vehiculo(
    request: Request,
    usuario_id: str,
    placa: str = Form(...),
    tipo: str = Form(...),
    marca: str = Form(...),
    modelo: str = Form(...),
    color: str = Form(...),
    estado: str = Form("Activo"),
    foto: Optional[UploadFile] = File(None),
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_vehiculos = RepositorioVehiculosBD(db, repo_usuarios)
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    
    user_context = obtener_contexto_usuario(request, db)
    tipos_info = [TipoVehiculoInfo.from_enum(t) for t in TipoVehiculo]

    if not usuario:
        return templates.TemplateResponse(
            "vehiculos/registrar.html",
            {
                "request": request, 
                "usuario": None, 
                "error": "Usuario no encontrado", 
                "tipos_vehiculo": list(TipoVehiculo),
                "tipos_info": tipos_info,
                "estados": list(EstadoVehiculo),
                "form_data": {},
                **user_context
            },
            status_code=404
        )
    
    caso_uso = RegistrarVehiculo(repo_vehiculos)
    try:
        await caso_uso.ejecutar(
            placa=placa,
            tipo=tipo,
            marca=marca,
            modelo=modelo,
            color=color,
            usuario=usuario,
            estado=estado,
            archivo_foto=foto
        )
        
    except ValueError as e:
        return templates.TemplateResponse(
            "vehiculos/registrar.html",
            {
                "request": request,
                "usuario": usuario,
                "error": str(e),
                "tipos_vehiculo": list(TipoVehiculo),
                "tipos_info": tipos_info,
                "estados": list(EstadoVehiculo),
                "form_data": {
                    "placa": placa,
                    "tipo": tipo,
                    "marca": marca,
                    "modelo": modelo,
                    "color": color,
                    "estado": estado
                },
                **user_context
            }
        )
    
    return RedirectResponse(
        url=f"/usuario/{usuario_id}/vehiculos",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get(
    "/usuario/{usuario_id}/vehiculos/{placa}",
    response_class=HTMLResponse,
    name="Ver detalle vehiculo"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def ver_detalle_vehiculo(
    request: Request,
    usuario_id: str,
    placa: str,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_vehiculos = RepositorioVehiculosBD(db, repo_usuarios)
    
    caso_uso = ObtenerVehiculo(repo_vehiculos)
    vehiculo = caso_uso.ejecutar(placa)
    
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    # Verificar que pertenece al usuario solicitado
    if vehiculo.usuario.numero_documento.valor != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse(
        "vehiculos/detalle.html",
        {
            "request": request,
            "vehiculo": vehiculo,
            "usuario": vehiculo.usuario,
            **user_context
        }
    )

@router.get(
    "/usuario/{usuario_id}/vehiculos/{placa}/editar",
    response_class=HTMLResponse,
    name="Mostrar formulario editar vehiculo"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def mostrar_formulario_editar_vehiculo(
    request: Request,
    usuario_id: str,
    placa: str,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_vehiculos = RepositorioVehiculosBD(db, repo_usuarios)
    
    caso_uso = ObtenerVehiculo(repo_vehiculos)
    vehiculo = caso_uso.ejecutar(placa)
    
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    # Verificar permisos
    if vehiculo.usuario.numero_documento.valor != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    tipos_info = [TipoVehiculoInfo.from_enum(tipo) for tipo in TipoVehiculo]
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse(
        "vehiculos/editar.html",
        {
            "request": request,
            "vehiculo": vehiculo,
            "usuario": vehiculo.usuario,
            "tipos_vehiculo": list(TipoVehiculo),
            "tipos_info": tipos_info,
            "estados": list(EstadoVehiculo),
            **user_context
        }
    )

@router.post(
    "/usuario/{usuario_id}/vehiculos/{placa}/editar",
    response_class=HTMLResponse,
    name="Actualizar vehiculo"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def actualizar_vehiculo_route(
    request: Request,
    usuario_id: str,
    placa: str,
    tipo: Optional[str] = Form(None),
    marca: Optional[str] = Form(None),
    modelo: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    estado: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    eliminar_foto: bool = Form(False),
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_vehiculos = RepositorioVehiculosBD(db, repo_usuarios)
    
    # Verificar que el vehículo existe y pertenece al usuario
    vehiculo_actual = repo_vehiculos.obtener_por_placa(placa)
    if not vehiculo_actual:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    if vehiculo_actual.usuario.numero_documento.valor != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    caso_uso = ActualizarVehiculo(repo_vehiculos)
    try:
        await caso_uso.ejecutar(
            placa=placa,
            tipo=tipo,
            marca=marca,
            modelo=modelo,
            color=color,
            estado=estado,
            archivo_foto=foto,
            eliminar_foto=eliminar_foto
        )
    except ValueError as e:
        user_context = obtener_contexto_usuario(request, db)
        tipos_info = [TipoVehiculoInfo.from_enum(t) for t in TipoVehiculo]
        
        return templates.TemplateResponse(
            "vehiculos/editar.html",
            {
                "request": request,
                "vehiculo": vehiculo_actual,
                "usuario": vehiculo_actual.usuario,
                "error": str(e),
                "tipos_vehiculo": list(TipoVehiculo),
                "tipos_info": tipos_info,
                "estados": list(EstadoVehiculo),
                **user_context
            }
        )
    
    return RedirectResponse(
        url=f"/usuario/{usuario_id}/vehiculos/{placa}",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post(
    "/usuario/{usuario_id}/vehiculos/{placa}/reactivar",
    response_class=HTMLResponse,
    name="Reactivar vehiculo"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def reactivar_vehiculo_route(
    request: Request,
    usuario_id: str,
    placa: str,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_vehiculos = RepositorioVehiculosBD(db, repo_usuarios)
    
    # Verificar que el vehículo existe y pertenece al usuario
    vehiculo = repo_vehiculos.obtener_por_placa(placa)
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    if vehiculo.usuario.numero_documento.valor != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Reactivar (cambiar estado a Activo)
    caso_uso = ActualizarVehiculo(repo_vehiculos)
    try:
        caso_uso.ejecutar_sin_archivo(
            placa=placa,
            estado="Activo"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return RedirectResponse(
        url=f"/usuario/{usuario_id}/vehiculos?incluir_inactivos=true",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post(
    "/usuario/{usuario_id}/vehiculos/{placa}/eliminar",
    response_class=HTMLResponse,
    name="Eliminar vehiculo"
)
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def eliminar_vehiculo_route(
    request: Request,
    usuario_id: str,
    placa: str,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_vehiculos = RepositorioVehiculosBD(db, repo_usuarios)
    
    # Verificar si el vehículo está activo para decidir si desactivar o eliminar
    vehiculo = repo_vehiculos.obtener_por_placa(placa)
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    if vehiculo.usuario.numero_documento.valor != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    if vehiculo.estado.value == "Activo":
        # Si está activo, solo desactivar (inactivar)
        caso_uso_actualizar = ActualizarVehiculo(repo_vehiculos)
        try:
            caso_uso_actualizar.ejecutar_sin_archivo(
                placa=placa,
                estado="Inactivo"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        return RedirectResponse(
            url=f"/usuario/{usuario_id}/vehiculos?incluir_inactivos=true",
            status_code=status.HTTP_303_SEE_OTHER
        )
    else:
        # Si ya está inactivo, eliminar permanentemente
        caso_uso = EliminarVehiculo(repo_vehiculos)
        try:
            caso_uso.ejecutar(placa, usuario_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        return RedirectResponse(
            url=f"/usuario/{usuario_id}/vehiculos",
            status_code=status.HTTP_303_SEE_OTHER
        )

# ======================== RUTAS API (JSON) ========================

@router.get(
    "/api/usuario/{usuario_id}/vehiculos",
    response_model=List[VehiculoResumen],
    name="API Listar vehiculos"
)
async def api_listar_vehiculos(
    usuario_id: str,
    buscar: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    incluir_inactivos: bool = Query(False),
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_vehiculos = RepositorioVehiculosBD(db, repo_usuarios)
    
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if buscar:
        vehiculos = repo_vehiculos.buscar_por_marca_modelo(buscar, usuario_id)
    elif tipo:
        vehiculos = repo_vehiculos.listar_por_tipo(tipo, incluir_inactivos)
        vehiculos = [v for v in vehiculos if v.usuario.numero_documento.valor == usuario_id]
    else:
        vehiculos = repo_vehiculos.listar_por_usuario(usuario_id, incluir_inactivos)
    
    return [VehiculoResumen.from_domain(v) for v in vehiculos]

@router.get(
    "/api/usuario/{usuario_id}/vehiculos/{placa}",
    response_model=VehiculoRead,
    name="API Obtener vehiculo"
)
async def api_obtener_vehiculo(
    usuario_id: str,
    placa: str,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_vehiculos = RepositorioVehiculosBD(db, repo_usuarios)
    
    caso_uso = ObtenerVehiculo(repo_vehiculos)
    vehiculo = caso_uso.ejecutar(placa)
    
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    if vehiculo.usuario.numero_documento.valor != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    return VehiculoRead.from_domain(vehiculo)

@router.get(
    "/api/usuario/{usuario_id}/vehiculos/estadisticas",
    response_model=EstadisticasVehiculos,
    name="API Estadísticas vehiculos"
)
async def api_estadisticas_vehiculos(
    usuario_id: str,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_vehiculos = RepositorioVehiculosBD(db, repo_usuarios)
    
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    estadisticas = repo_vehiculos.contar_por_usuario(usuario_id)
    return EstadisticasVehiculos(**estadisticas)

@router.get(
    "/api/tipos-vehiculo",
    response_model=List[TipoVehiculoInfo],
    name="API Tipos de vehiculo"
)
async def api_tipos_vehiculo():
    return [TipoVehiculoInfo.from_enum(tipo) for tipo in TipoVehiculo]

@router.post(
    "/api/usuario/{usuario_id}/vehiculos/{placa}/subir-foto",
    name="API Subir foto vehiculo"
)
async def api_subir_foto_vehiculo(
    usuario_id: str,
    placa: str,
    foto: UploadFile = File(...),
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_vehiculos = RepositorioVehiculosBD(db, repo_usuarios)
    
    # Verificar vehículo por placa
    vehiculo = repo_vehiculos.obtener_por_placa(placa)
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    if vehiculo.usuario.numero_documento.valor != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Actualizar con nueva foto
    caso_uso = ActualizarVehiculo(repo_vehiculos)
    try:
        await caso_uso.ejecutar(
            placa=placa,
            archivo_foto=foto
        )
        
        # Obtener vehículo actualizado para retornar URL
        vehiculo_actualizado = repo_vehiculos.obtener_por_placa(placa)
        return {
            "success": True,
            "foto_url": vehiculo_actualizado.foto.obtener_url_publica(),
            "message": "Foto subida correctamente"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))