'''
Rutas del módulo QR Acceso
'''
from fastapi import (
    APIRouter,
    Request,
    Depends,
    Form,
    HTTPException,
    status,
)
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import and_


# Core dependencies
from app.core.dependencias.dependencias import get_db
from app.core.resources.templates import templates
from app.core.utils.contexto_usuario import obtener_contexto_usuario

# Repositorios
from app.modules.qr_acceso.infrastructure.repositorios.repositorio import RepositorioQRAccesoBD
from app.modules.autenticacion.infrastructure.repositorios.repositorio import RepositorioUsuariosBD
from app.modules.pertenencias.infrastructure.repositorios.repositorio import RepositorioPertenenciasBD
from app.modules.vehiculos.infrastructure.repositorios.repositorio import RepositorioVehiculosBD

# Casos de uso
from app.modules.qr_acceso.application.casos_de_uso.generar_qr_usuario import GenerarQRUsuario

# Esquemas
from app.modules.qr_acceso.interface.esquemas import (
    QRGenerarRequest, QRGenerarResponse, QRValidarRequest, QRValidarResponse,
    AccesoProcesarRequest, AccesoProcesarResponse, RegistroAccesoRead,
    EstadisticasAcceso, DashboardVigilanteData, ErrorQRResponse
)

# Validadores de autenticación
from app.modules.auth.validadores.token_cookie import validar_token_cookie
from app.modules.auth.validadores.roles import rol_requerido_cookie

router = APIRouter(tags=["qr_acceso"], prefix="/qr-acceso")

# ======================== FUNCIONES AUXILIARES ========================

def obtener_repositorios(db: Session):
    """Obtiene todos los repositorios necesarios"""
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_qr = RepositorioQRAccesoBD(db, repo_usuarios)
    repo_pertenencias = RepositorioPertenenciasBD(db, repo_usuarios)
    repo_vehiculos = RepositorioVehiculosBD(db, repo_usuarios)
    
    return repo_usuarios, repo_qr, repo_pertenencias, repo_vehiculos

# ======================== RUTAS PARA USUARIOS ========================

@router.get("/usuario/{usuario_id}/mi-qr", response_class=HTMLResponse, name="Ver QR del usuario")
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def ver_qr_usuario(
    request: Request, 
    usuario_id: str,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    """Página para que el usuario vea y genere su QR de acceso"""
    repo_usuarios, repo_qr, _, _ = obtener_repositorios(db)
    
    # Verificar que el usuario existe
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar permisos (usuario puede ver su propio QR o admin puede ver cualquiera)
    if current_user_id != usuario_id:
        current_user = repo_usuarios.obtener_por_id(current_user_id)
        if not current_user or current_user.rol.value not in ["Superadministrador", "Administrador"]:
            raise HTTPException(status_code=403, detail="No autorizado")
    
    # Obtener estado actual del usuario
    ultimo_registro = repo_qr.obtener_ultimo_registro_usuario(usuario_id)
    estado_actual = "FUERA"
    if ultimo_registro:
        if ultimo_registro.tipo_movimiento == "INGRESO":
            estado_actual = "DENTRO"
        else:
            estado_actual = "FUERA"
    
    # Obtener QRs activos
    qrs_activos = repo_qr.obtener_qrs_activos_usuario(usuario_id)
    
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse("qr_acceso/mi_qr.html", {
        "request": request,
        "usuario": usuario,
        "estado_actual": estado_actual,
        "ultimo_registro": ultimo_registro,
        "qrs_activos": qrs_activos,
        **user_context
    })

@router.post("/usuario/{usuario_id}/generar", response_model=QRGenerarResponse, name="Generar QR de acceso")
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def generar_qr_acceso(
    request: Request,
    usuario_id: str,
    duracion_minutos: int = Form(15),
    incluir_pertenencias: bool = Form(True),
    incluir_vehiculos: bool = Form(True),
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    """Genera un QR de acceso para el usuario"""
    repo_usuarios, repo_qr, repo_pertenencias, repo_vehiculos = obtener_repositorios(db)
    
    # Verificar usuario
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar permisos
    if current_user_id != usuario_id:
        current_user = repo_usuarios.obtener_por_id(current_user_id)
        if not current_user or current_user.rol.value not in ["Superadministrador", "Administrador"]:
            raise HTTPException(status_code=403, detail="No autorizado")
    
    try:
        # Usar caso de uso
        caso_uso = GenerarQRUsuario(repo_qr, repo_pertenencias, repo_vehiculos)
        qr_acceso, imagen_base64 = caso_uso.ejecutar(
            usuario=usuario,
            duracion_minutos=duracion_minutos,
            incluir_pertenencias=incluir_pertenencias,
            incluir_vehiculos=incluir_vehiculos
        )
        
        return QRGenerarResponse(
            qr_id=qr_acceso.id,
            token_jwt=qr_acceso.token_jwt,
            imagen_base64=imagen_base64,
            fecha_expiracion=qr_acceso.fecha_expiracion,
            duracion_minutos=qr_acceso.duracion_minutos,
            pertenencias_incluidas=qr_acceso.pertenencias_incluidas,
            vehiculos_incluidos=qr_acceso.vehiculos_incluidos,
            segundos_restantes=qr_acceso.segundos_restantes,
            mensaje=f"QR generado exitosamente. Válido por {duracion_minutos} minutos."
        )
        
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content=ErrorQRResponse.crear_error(str(e), "GENERAR_QR_ERROR").dict()
        )

@router.get("/usuario/{usuario_id}/historial", response_class=HTMLResponse, name="Historial de accesos del usuario")
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def historial_accesos_usuario(
    request: Request,
    usuario_id: str,
    dias: int = 30,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    """Página de historial de accesos del usuario"""
    repo_usuarios, repo_qr, _, _ = obtener_repositorios(db)
    
    # Verificar usuario
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar permisos
    if current_user_id != usuario_id:
        current_user = repo_usuarios.obtener_por_id(current_user_id)
        if not current_user or current_user.rol.value not in ["Superadministrador", "Administrador"]:
            raise HTTPException(status_code=403, detail="No autorizado")
    
    # Obtener registros
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=dias)
    registros = repo_qr.listar_registros_por_fecha(fecha_inicio, fecha_fin, usuario_id)
    
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse("qr_acceso/historial_usuario.html", {
        "request": request,
        "usuario": usuario,
        "registros": registros,
        "dias": dias,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        **user_context
    })

# ======================== RUTAS PARA VIGILANTES ========================

@router.get("/vigilante/scanner", response_class=HTMLResponse, name="Scanner QR para vigilantes")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante", "Aprendiz")
async def scanner_qr_vigilante(
    request: Request,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    """Página del scanner QR para vigilantes"""
    user_context = obtener_contexto_usuario(request, db)
    return templates.TemplateResponse("qr_acceso/scanner_vigilante.html", {
        "request": request,
        **user_context
    })

@router.post("/vigilante/validar", response_model=QRValidarResponse, name="Validar QR sin procesar")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante", "Aprendiz")
async def validar_qr_acceso(
    request: Request,  # ← AGREGAR ESTO como primer parámetro
    token_jwt: str = Form(...),
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    """Valida un QR sin procesarlo (para mostrar información al vigilante)"""
    repo_usuarios, repo_qr, _, _ = obtener_repositorios(db)
    
    try:
        # Obtener QR por JWT
        qr_acceso = repo_qr.obtener_qr_por_jwt(token_jwt)
        if not qr_acceso:
            return QRValidarResponse(
                valido=False,
                mensaje="QR no válido o no encontrado"
            )
        
        # Verificar que puede usarse
        if not qr_acceso.puede_usarse:
            mensaje = "QR ya usado" if qr_acceso.usado else "QR expirado"
            return QRValidarResponse(
                valido=False,
                mensaje=mensaje
            )
        
        # Determinar estado actual y siguiente movimiento
        ultimo_registro = repo_qr.obtener_ultimo_registro_usuario(qr_acceso.usuario.numero_documento.valor)
        
        if not ultimo_registro or ultimo_registro.tipo_movimiento == "SALIDA":
            estado_actual = "FUERA"
            siguiente_movimiento = "INGRESO"
        else:
            estado_actual = "DENTRO"
            siguiente_movimiento = "SALIDA"
        
        return QRValidarResponse(
            valido=True,
            usuario_id=qr_acceso.usuario.numero_documento.valor,
            nombre_completo=f"{qr_acceso.usuario.nombres.valor} {qr_acceso.usuario.apellidos.valor}",
            rol=qr_acceso.usuario.rol.value,
            estado_actual=estado_actual,
            siguiente_movimiento=siguiente_movimiento,
            pertenencias_incluidas=qr_acceso.pertenencias_incluidas,
            vehiculos_incluidos=qr_acceso.vehiculos_incluidos,
            segundos_restantes=qr_acceso.segundos_restantes,
            mensaje=f"QR válido para {siguiente_movimiento.lower()}"
        )
        
    except Exception as e:
        return QRValidarResponse(
            valido=False,
            mensaje=f"Error validando QR: {str(e)}"
        )

@router.post("/vigilante/procesar", response_model=AccesoProcesarResponse, name="Procesar acceso con QR")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante", "Aprendiz")
async def procesar_acceso_qr(
    token_jwt: str = Form(...),
    ubicacion: str = Form("Entrada Principal"),
    observaciones: str = Form(""),
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    """Procesa el acceso usando un QR válido"""
    repo_usuarios, repo_qr, _, _ = obtener_repositorios(db)
    
    try:
        # Obtener y validar QR
        qr_acceso = repo_qr.obtener_qr_por_jwt(token_jwt)
        if not qr_acceso:
            raise ValueError("QR no válido o no encontrado")
        
        if not qr_acceso.puede_usarse:
            raise ValueError("QR ya usado o expirado")
        
        # Determinar tipo de movimiento
        ultimo_registro = repo_qr.obtener_ultimo_registro_usuario(qr_acceso.usuario.numero_documento.valor)
        
        if not ultimo_registro or ultimo_registro.tipo_movimiento == "SALIDA":
            tipo_movimiento = "INGRESO"
            nuevo_estado = "DENTRO"
        else:
            tipo_movimiento = "SALIDA"
            nuevo_estado = "FUERA"
        
        # Crear registro de acceso
        from app.modules.qr_acceso.domain.entidades.registro_acceso import RegistroAcceso
        
        registro = RegistroAcceso(
            usuario=qr_acceso.usuario,
            tipo_movimiento=tipo_movimiento,
            fecha_hora=datetime.now(),
            vigilante_id=current_user_id,
            ubicacion=ubicacion,
            pertenencias_declaradas=qr_acceso.pertenencias_incluidas,
            vehiculos_declarados=qr_acceso.vehiculos_incluidos,
            observaciones=observaciones.strip(),
            qr_usado_id=qr_acceso.id
        )
        
        # Guardar registro
        repo_qr.guardar_registro(registro)
        
        # Marcar QR como usado
        repo_qr.marcar_qr_usado(qr_acceso.id, current_user_id, ubicacion)
        
        return AccesoProcesarResponse(
            success=True,
            registro_id=registro.id,
            tipo_movimiento=tipo_movimiento,
            usuario_nombre=f"{qr_acceso.usuario.nombres.valor} {qr_acceso.usuario.apellidos.valor}",
            fecha_hora=registro.fecha_hora,
            pertenencias_procesadas=qr_acceso.pertenencias_incluidas,
            vehiculos_procesados=qr_acceso.vehiculos_incluidos,
            nuevo_estado=nuevo_estado,
            mensaje=f"✅ {tipo_movimiento.capitalize()} registrado exitosamente"
        )
        
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content=ErrorQRResponse.crear_error(str(e), "PROCESAR_ACCESO_ERROR").dict()
        )

@router.get("/vigilante/dashboard", response_class=HTMLResponse, name="Dashboard de vigilancia")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante", "Aprendiz")
async def dashboard_vigilante(
    request: Request,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    """Dashboard para vigilantes con estadísticas y accesos recientes"""
    repo_usuarios, repo_qr, _, _ = obtener_repositorios(db)
    
    # Obtener estadísticas del día
    stats = repo_qr.contar_registros_hoy()
    
    # Obtener usuarios dentro
    usuarios_dentro = repo_qr.obtener_usuarios_dentro()
    
    # Obtener registros recientes (últimas 2 horas)
    hace_dos_horas = datetime.now() - timedelta(hours=2)
    registros_recientes = repo_qr.listar_registros_por_fecha(hace_dos_horas, datetime.now())
    registros_recientes = registros_recientes[:10]  # Solo los 10 más recientes
    
    # Contar QRs activos (simplificado)
    from app.modules.qr_acceso.infrastructure.modelos.modelo_qr_acceso import QRAccesoORM
    qrs_activos = db.query(QRAccesoORM).filter(
        and_(
            QRAccesoORM.usado == False,
            QRAccesoORM.fecha_expiracion > datetime.now()
        )
    ).count()
    
    # Crear estadísticas completas
    estadisticas = EstadisticasAcceso(
        total_hoy=stats["total"],
        ingresos_hoy=stats["ingresos"],
        salidas_hoy=stats["salidas"],
        dentro_estimado=stats["dentro_estimado"],
        usuarios_dentro=usuarios_dentro,
        qrs_activos=qrs_activos
    )
    
    # Generar alertas
    alertas = []
    if len(usuarios_dentro) > 50:
        alertas.append(f"Alto número de personas dentro: {len(usuarios_dentro)}")
    
    for usuario in usuarios_dentro:
        if usuario["tiempo_dentro_minutos"] > 480:  # 8 horas
            alertas.append(f"{usuario['nombre']} lleva {usuario['tiempo_dentro_minutos']//60} horas dentro")
    
    dashboard_data = DashboardVigilanteData(
        estadisticas=estadisticas,
        registros_recientes=[RegistroAccesoRead.from_domain(r) for r in registros_recientes],
        alertas=alertas
    )
    
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse("qr_acceso/dashboard_vigilante.html", {
        "request": request,
        "dashboard": dashboard_data,
        "usuarios_dentro_count": len(usuarios_dentro),
        **user_context
    })

# ======================== RUTAS PARA ADMINISTRADORES ========================

@router.get("/admin/panel", response_class=HTMLResponse, name="Panel administrativo QR")
@rol_requerido_cookie("Superadministrador", "Administrador")
async def panel_admin_qr(
    request: Request,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    """Panel administrativo para gestión de QR y accesos"""
    repo_usuarios, repo_qr, _, _ = obtener_repositorios(db)
    
    # Estadísticas generales
    stats_hoy = repo_qr.contar_registros_hoy()
    usuarios_dentro = repo_qr.obtener_usuarios_dentro()
    
    # Estadísticas de la semana
    hace_semana = datetime.now() - timedelta(days=7)
    registros_semana = repo_qr.listar_registros_por_fecha(hace_semana, datetime.now())
    
    # QRs activos
    from app.modules.qr_acceso.infrastructure.modelos.modelo_qr_acceso import QRAccesoORM
    qrs_activos = db.query(QRAccesoORM).filter(
        and_(
            QRAccesoORM.usado == False,
            QRAccesoORM.fecha_expiracion > datetime.now()
        )
    ).count()
    
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse("qr_acceso/panel_admin.html", {
        "request": request,
        "stats_hoy": stats_hoy,
        "usuarios_dentro": usuarios_dentro,
        "registros_semana_count": len(registros_semana),
        "qrs_activos": qrs_activos,
        **user_context
    })

@router.get("/admin/registros", response_class=HTMLResponse, name="Todos los registros de acceso")
@rol_requerido_cookie("Superadministrador", "Administrador")
async def listar_todos_registros(
    request: Request,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    usuario_id: Optional[str] = None,
    tipo_movimiento: Optional[str] = None,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    """Lista todos los registros de acceso con filtros"""
    repo_usuarios, repo_qr, _, _ = obtener_repositorios(db)
    
    # Procesar fechas
    if not fecha_fin:
        fecha_fin_dt = datetime.now()
    else:
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
    
    if not fecha_inicio:
        fecha_inicio_dt = fecha_fin_dt - timedelta(days=7)  # Última semana por defecto
    else:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    
    # Obtener registros
    registros = repo_qr.listar_registros_por_fecha(fecha_inicio_dt, fecha_fin_dt, usuario_id)
    
    # Filtrar por tipo si se especifica
    if tipo_movimiento:
        registros = [r for r in registros if r.tipo_movimiento == tipo_movimiento]
    
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse("qr_acceso/admin_registros.html", {
        "request": request,
        "registros": registros,
        "fecha_inicio": fecha_inicio_dt,
        "fecha_fin": fecha_fin_dt,
        "usuario_filtro": usuario_id,
        "tipo_filtro": tipo_movimiento,
        "total_registros": len(registros),
        **user_context
    })

@router.get("/admin/usuarios-dentro", response_class=HTMLResponse, name="Usuarios actualmente dentro")
@rol_requerido_cookie("Superadministrador", "Administrador")
async def usuarios_dentro_admin(
    request: Request,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    """Página que muestra usuarios que están actualmente dentro"""
    repo_usuarios, repo_qr, _, _ = obtener_repositorios(db)
    
    usuarios_dentro = repo_qr.obtener_usuarios_dentro()
    
    # Procesar para agregar información adicional
    usuarios_procesados = []
    for usuario_info in usuarios_dentro:
        tiempo_horas = round(usuario_info["tiempo_dentro_minutos"] / 60, 1)
        
        # Clasificar por tiempo
        if tiempo_horas < 4:
            categoria = "normal"
        elif tiempo_horas < 8:
            categoria = "largo"
        else:
            categoria = "muy_largo"
        
        usuarios_procesados.append({
            **usuario_info,
            "tiempo_dentro_horas": tiempo_horas,
            "categoria_tiempo": categoria
        })
    
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse("qr_acceso/usuarios_dentro.html", {
        "request": request,
        "usuarios_dentro": usuarios_procesados,
        "total_dentro": len(usuarios_procesados),
        **user_context
    })

# ======================== API ENDPOINTS ========================

@router.get("/api/estadisticas", response_model=EstadisticasAcceso, name="API Estadísticas")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante")
async def api_estadisticas(
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    """API para obtener estadísticas de acceso"""
    repo_usuarios, repo_qr, _, _ = obtener_repositorios(db)
    
    stats = repo_qr.contar_registros_hoy()
    usuarios_dentro = repo_qr.obtener_usuarios_dentro()
    
    # Contar QRs activos
    from app.modules.qr_acceso.infrastructure.modelos.modelo_qr_acceso import QRAccesoORM
    qrs_activos = db.query(QRAccesoORM).filter(
        and_(
            QRAccesoORM.usado == False,
            QRAccesoORM.fecha_expiracion > datetime.now()
        )
    ).count()
    
    return EstadisticasAcceso(
        total_hoy=stats["total"],
        ingresos_hoy=stats["ingresos"],
        salidas_hoy=stats["salidas"],
        dentro_estimado=stats["dentro_estimado"],
        usuarios_dentro=usuarios_dentro,
        qrs_activos=qrs_activos
    )

@router.get("/api/registros", name="API Listar registros")
@rol_requerido_cookie("Superadministrador", "Administrador")
async def api_listar_registros(
    fecha_inicio: str,
    fecha_fin: str,
    usuario_id: Optional[str] = None,
    tipo_movimiento: Optional[str] = None,
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    """API para obtener registros de acceso"""
    repo_usuarios, repo_qr, _, _ = obtener_repositorios(db)
    
    try:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido (YYYY-MM-DD)")
    
    registros = repo_qr.listar_registros_por_fecha(fecha_inicio_dt, fecha_fin_dt, usuario_id)
    
    if tipo_movimiento:
        registros = [r for r in registros if r.tipo_movimiento == tipo_movimiento]
    
    return [RegistroAccesoRead.from_domain(r) for r in registros]

@router.post("/api/limpiar-qrs-expirados", name="API Limpiar QRs expirados")
@rol_requerido_cookie("Superadministrador", "Administrador")
async def api_limpiar_qrs_expirados(
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    """API para limpiar QRs expirados"""
    repo_usuarios, repo_qr, _, _ = obtener_repositorios(db)
    
    eliminados = repo_qr.limpiar_qrs_expirados()
    
    return {
        "success": True,
        "qrs_eliminados": eliminados,
        "mensaje": f"Se eliminaron {eliminados} QRs expirados"
    }

@router.get("/api/usuarios-dentro", name="API Usuarios dentro")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante")
async def api_usuarios_dentro(
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    """API para obtener usuarios que están dentro"""
    repo_usuarios, repo_qr, _, _ = obtener_repositorios(db)
    
    usuarios_dentro = repo_qr.obtener_usuarios_dentro()
    
    return {
        "total": len(usuarios_dentro),
        "usuarios": usuarios_dentro
    }


