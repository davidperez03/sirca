from fastapi import (
    APIRouter,
    Request,
    Depends,
    Form,
    Query,
    HTTPException,
    status,
    BackgroundTasks,
    WebSocket
)
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import asyncio

# Core dependencies
from app.core.dependencias.dependencias import get_db
from app.core.resources.templates import templates
from app.core.utils.contexto_usuario import obtener_contexto_usuario

# Repositorios
from app.modules.qr_control.infrastructure.repositorios.repositorio import RepositorioAccesosBD
from app.modules.autenticacion.infrastructure.repositorios.repositorio import RepositorioUsuariosBD

# Casos de uso
from app.modules.qr_control.application.casos_de_uso.generar_qr_temporal import GenerarQRTemporal
from app.modules.qr_control.application.casos_de_uso.procesar_acceso_qr import ProcesarAccesoQR
from app.modules.qr_control.application.casos_de_uso.consultar_accesos import ConsultarAccesos

# Servicio principal
from app.modules.qr_control.application.servicios.servicio_qr_control import ServicioQRControl

# Esquemas
from app.modules.qr_control.interface.esquemas import (
    QRTemporalCreate, QRTemporalResponse, AccesoCreate, AccesoRead,
    ValidacionQRResponse, ReporteDiario, EstadisticasGenerales,
    ProcesarAccesoResponse, ErrorResponse, DashboardData, QRTemporalRead
)

# Validadores de autenticación
from app.modules.auth.validadores.token_cookie import validar_token_cookie
from app.modules.auth.validadores.roles import rol_requerido_cookie

router = APIRouter(tags=["qr_control"])

# ======================== RUTAS PARA USUARIOS ========================

@router.get("/usuario/{usuario_id}/qr", response_class=HTMLResponse, name="Ver QR del usuario")
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def ver_qr_usuario(request: Request, usuario_id: str, current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if current_user_id != usuario_id:
        current_user = repo_usuarios.obtener_por_id(current_user_id)
        if not current_user or current_user.rol.value not in ["Superadministrador", "Administrador"]:
            raise HTTPException(status_code=403, detail="No autorizado")
    
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    estado_actual = servicio.obtener_estado_usuario(usuario_id)
    ultimo_acceso = servicio.obtener_ultimo_acceso_usuario(usuario_id)
    
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse("qr_control/qr_usuario.html", {
        "request": request, "usuario": usuario, "estado_actual": estado_actual, "ultimo_acceso": ultimo_acceso, **user_context
    })

@router.post("/usuario/{usuario_id}/qr/generar", name="Generar QR temporal")
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def generar_qr_temporal(
    request: Request,  # 👈 Agrega esto
    usuario_id: str,
    duracion_minutos: int = Form(5),
    current_user_id: str = Depends(validar_token_cookie),
    db: Session = Depends(get_db)
):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if current_user_id != usuario_id:
        current_user = repo_usuarios.obtener_por_id(current_user_id)
        if not current_user or current_user.rol.value not in ["Superadministrador", "Administrador"]:
            raise HTTPException(status_code=403, detail="No autorizado")
    
    if not usuario.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    
    if not 1 <= duracion_minutos <= 60:
        raise HTTPException(status_code=400, detail="Duración debe estar entre 1 y 60 minutos")
    
    try:
        servicio = ServicioQRControl(repo_accesos, repo_usuarios)
        qr_temporal, imagen_base64 = servicio.generar_qr_usuario(usuario_id, duracion_minutos)
        
        return JSONResponse({
            "success": True,
            "qr_data": {
                "codigo": qr_temporal.codigo_qr,
                "expira_en": int((qr_temporal.fecha_expiracion - datetime.now()).total_seconds()),
                "fecha_expiracion": qr_temporal.fecha_expiracion.isoformat()
            },
            "qr_image": imagen_base64,
            "message": f"QR generado exitosamente. Válido por {duracion_minutos} minutos."
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/usuario/{usuario_id}/accesos", response_class=HTMLResponse, name="Ver historial de accesos del usuario")
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def ver_accesos_usuario(request: Request, usuario_id: str, dias: int = Query(30, description="Días hacia atrás"), current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if current_user_id != usuario_id:
        current_user = repo_usuarios.obtener_por_id(current_user_id)
        if not current_user or current_user.rol.value not in ["Superadministrador", "Administrador"]:
            raise HTTPException(status_code=403, detail="No autorizado")
    
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    accesos = servicio.obtener_accesos_usuario(usuario_id, dias)
    
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse("qr_control/accesos_usuario.html", {
        "request": request, "usuario": usuario, "accesos": accesos, "dias": dias,
        "fecha_inicio": datetime.now() - timedelta(days=dias), "fecha_fin": datetime.now(), **user_context
    })

# ======================== RUTAS PARA VIGILANTES ========================

@router.get("/vigilante/scanner", response_class=HTMLResponse, name="Scanner QR para vigilantes")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante", "Aprendiz")
async def scanner_qr(request: Request, current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    user_context = obtener_contexto_usuario(request, db)
    return templates.TemplateResponse("qr_control/scanner.html", {"request": request, **user_context})

@router.post("/vigilante/validar-qr", name="Validar QR sin procesar")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante", "Aprendiz")
async def validar_qr(codigo_qr: str = Form(...), current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    try:
        servicio = ServicioQRControl(repo_accesos, repo_usuarios)
        info = await servicio.validar_qr_codigo(codigo_qr)
        return ValidacionQRResponse(valido=True, mensaje=f"QR válido para {info['nombre_completo']}", **info)
    except ValueError as e:
        return ValidacionQRResponse(valido=False, mensaje=str(e))

@router.post("/api/vigilante/procesar-acceso", response_model=ProcesarAccesoResponse, name="API Procesar acceso")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante")
async def api_procesar_acceso(acceso_data: AccesoCreate, current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    try:
        servicio = ServicioQRControl(repo_accesos, repo_usuarios)
        registro = await servicio.procesar_acceso_qr(codigo_qr=acceso_data.codigo_qr, vigilante_id=current_user_id, ubicacion=acceso_data.ubicacion, items_declarados=acceso_data.items_declarados, observaciones=acceso_data.observaciones)
        nuevo_estado = servicio.obtener_estado_usuario(registro.usuario.numero_documento.valor)
        return ProcesarAccesoResponse.success_response(registro, nuevo_estado)
    except ValueError as e:
        return ProcesarAccesoResponse(success=False, registro=None, mensaje=str(e), nuevo_estado="")

# ======================== WEBSOCKET PARA TIEMPO REAL ========================

@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        repo_usuarios = RepositorioUsuariosBD(db)
        repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
        servicio = ServicioQRControl(repo_accesos, repo_usuarios)
        
        while True:
            try:
                dashboard_data = servicio.obtener_dashboard_data()
                await websocket.send_json({"type": "dashboard_update", "data": dashboard_data})
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Error enviando datos WebSocket: {e}")
                break
    except Exception as e:
        print(f"Error en WebSocket: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

@router.websocket("/ws/accesos")
async def websocket_accesos(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(5)
            sample_event = {
                "type": "nuevo_acceso",
                "timestamp": datetime.now().isoformat(),
                "usuario": "Usuario Ejemplo",
                "movimiento": "INGRESO"
            }
            await websocket.send_json(sample_event)
    except Exception as e:
        print(f"Error en WebSocket accesos: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

# ======================== RUTAS DE MANTENIMIENTO ========================

@router.post("/admin/mantenimiento/limpiar-registros-antiguos", name="Limpiar registros antiguos")
@rol_requerido_cookie("Superadministrador")
async def limpiar_registros_antiguos(dias: int = Query(365, description="Días de antigüedad para eliminar"), current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    if dias < 30:
        raise HTTPException(status_code=400, detail="No se pueden eliminar registros con menos de 30 días")
    
    fecha_limite = datetime.now() - timedelta(days=dias)
    return JSONResponse({"success": True, "mensaje": f"Proceso de limpieza iniciado para registros anteriores a {fecha_limite.strftime('%Y-%m-%d')}"})

@router.get("/admin/estadisticas/resumen-sistema", name="Resumen completo del sistema")
@rol_requerido_cookie("Superadministrador", "Administrador")
async def resumen_sistema(current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    estadisticas_generales = servicio.obtener_estadisticas_generales()
    reporte_semanal = servicio.generar_reporte_semanal()
    personas_dentro = servicio.obtener_personas_dentro_ahora()
    
    fecha_mes_pasado = datetime.now() - timedelta(days=30)
    accesos_mes = servicio.obtener_accesos_periodo(fecha_mes_pasado, datetime.now())
    usuarios_activos_mes = len(set(a.usuario.numero_documento.valor for a in accesos_mes))
    
    return JSONResponse({
        "estadisticas_generales": estadisticas_generales,
        "reporte_semanal": reporte_semanal,
        "personas_dentro_ahora": len(personas_dentro),
        "usuarios_activos_mes": usuarios_activos_mes,
        "total_accesos_mes": len(accesos_mes),
        "promedio_accesos_dia": len(accesos_mes) / 30,
        "ultima_actualizacion": datetime.now().isoformat()
    })

# ======================== RUTAS DE AYUDA Y DOCUMENTACIÓN ========================

@router.get("/api/info", name="Información del sistema QR")
async def info_sistema():
    return JSONResponse({
        "nombre": "Sistema de Control QR",
        "version": "1.0.0",
        "descripcion": "Sistema de control de acceso mediante códigos QR temporales",
        "endpoints": {
            "usuarios": "/usuario/{id}/qr - Generar QR personal",
            "vigilantes": "/vigilante/scanner - Scanner QR",
            "admin": "/admin/dashboard - Panel administrativo"
        },
        "estado": "activo",
        "ultima_actualizacion": datetime.now().isoformat()
    })

@router.get("/api/salud", name="Estado de salud del sistema")
async def salud_sistema(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        repo_usuarios = RepositorioUsuariosBD(db)
        repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
        estadisticas = ConsultarAccesos(repo_accesos).obtener_estadisticas_generales()
        
        return JSONResponse({
            "estado": "saludable",
            "base_de_datos": "conectada",
            "servicios": "funcionando",
            "accesos_hoy": estadisticas.get("accesos_hoy", 0),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "estado": "error",
            "mensaje": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=500)

@router.post("/vigilante/validar-qr", response_model=ValidacionQRResponse, name="API Validar QR")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante")
async def api_validar_qr(codigo_qr: str, current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)

    try:
        servicio = ServicioQRControl(repo_accesos, repo_usuarios)
        info = await servicio.validar_qr_codigo(codigo_qr)
        return ValidacionQRResponse(valido=True, mensaje=f"QR válido para {info['nombre_completo']}", **info)
    except ValueError as e:
        return ValidacionQRResponse(valido=False, mensaje=str(e))

@router.post("/vigilante/procesar-acceso", name="Procesar acceso con QR")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante")
async def procesar_acceso(background_tasks: BackgroundTasks, codigo_qr: str = Form(...), ubicacion: str = Form("Entrada Principal"), items_declarados: str = Form(""), observaciones: str = Form(""), current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    items_list = []
    if items_declarados.strip():
        items_list = [item.strip() for item in items_declarados.split(",") if item.strip()]
    
    try:
        servicio = ServicioQRControl(repo_accesos, repo_usuarios)
        registro = await servicio.procesar_acceso_qr(codigo_qr=codigo_qr, vigilante_id=current_user_id, ubicacion=ubicacion, items_declarados=items_list, observaciones=observaciones)
        nuevo_estado = servicio.obtener_estado_usuario(registro.usuario.numero_documento.valor)
        
        return JSONResponse({
            "success": True,
            "registro": AccesoRead.from_domain(registro).dict(),
            "mensaje": f"✅ {registro.tipo_movimiento.lower().capitalize()} registrado correctamente",
            "nuevo_estado": nuevo_estado
        })
    except ValueError as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)

@router.get("/vigilante/dashboard", response_class=HTMLResponse, name="Dashboard de vigilancia")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante")
async def dashboard_vigilante(request: Request, current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    estadisticas = servicio.obtener_estadisticas_generales()
    accesos_hoy = servicio.obtener_accesos_hoy()
    accesos_recientes = servicio.obtener_accesos_recientes(30)
    
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse("qr_control/dashboard_vigilante.html", {
        "request": request, "estadisticas": estadisticas, "accesos_hoy": accesos_hoy[:10], "accesos_recientes": accesos_recientes, **user_context
    })

# ======================== RUTAS PARA ADMINISTRADORES ========================

@router.get("/admin/reportes", response_class=HTMLResponse, name="Reportes de acceso")
@rol_requerido_cookie("Superadministrador", "Administrador")
async def reportes_acceso(request: Request, fecha: Optional[str] = Query(None, description="Fecha en formato YYYY-MM-DD"), current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    if fecha:
        try:
            fecha_reporte = datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido")
    else:
        fecha_reporte = datetime.now()
    
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    reporte = servicio.generar_reporte_diario(fecha_reporte)
    
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse("qr_control/reportes.html", {
        "request": request, "reporte": reporte, "fecha_seleccionada": fecha_reporte, **user_context
    })

@router.get("/admin/accesos", response_class=HTMLResponse, name="Lista de todos los accesos")
@rol_requerido_cookie("Superadministrador", "Administrador")
async def listar_todos_accesos(request: Request, fecha_inicio: Optional[str] = Query(None), fecha_fin: Optional[str] = Query(None), usuario_id: Optional[str] = Query(None), tipo_movimiento: Optional[str] = Query(None), current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    if not fecha_fin:
        fecha_fin_dt = datetime.now()
    else:
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
    
    if not fecha_inicio:
        fecha_inicio_dt = fecha_fin_dt - timedelta(days=30)
    else:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    accesos = servicio.obtener_accesos_periodo(fecha_inicio_dt, fecha_fin_dt)
    
    if usuario_id:
        accesos = [a for a in accesos if a.usuario.numero_documento.valor == usuario_id]
    
    if tipo_movimiento:
        accesos = [a for a in accesos if a.tipo_movimiento == tipo_movimiento]
    
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse("qr_control/admin_accesos.html", {
        "request": request, "accesos": accesos, "fecha_inicio": fecha_inicio_dt, "fecha_fin": fecha_fin_dt,
        "usuario_filtro": usuario_id, "tipo_filtro": tipo_movimiento, **user_context
    })

@router.get("/admin/dashboard", response_class=HTMLResponse, name="Dashboard administrativo")
@rol_requerido_cookie("Superadministrador", "Administrador")
async def dashboard_admin(request: Request, current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    estadisticas = servicio.obtener_estadisticas_generales()
    reporte_hoy = servicio.generar_reporte_diario()
    accesos_recientes = servicio.obtener_accesos_recientes(60)
    dashboard_data = servicio.obtener_dashboard_data()
    
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse("qr_control/dashboard_admin.html", {
        "request": request, "estadisticas": estadisticas, "reporte_hoy": reporte_hoy,
        "accesos_recientes": accesos_recientes, "alertas": dashboard_data.get('alertas', []), **user_context
    })

@router.get("/admin/usuarios-estado", response_class=HTMLResponse, name="Estado de usuarios")
@rol_requerido_cookie("Superadministrador", "Administrador")
async def estado_usuarios(request: Request, current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    personas_dentro = servicio.obtener_personas_dentro_ahora()
    
    user_context = obtener_contexto_usuario(request, db)
    
    return templates.TemplateResponse("qr_control/estado_usuarios.html", {
        "request": request, "personas_dentro": personas_dentro, "total_dentro": len(personas_dentro), **user_context
    })

# ======================== API ENDPOINTS ========================

@router.get("/api/accesos/estadisticas", response_model=EstadisticasGenerales, name="API Estadísticas generales")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante")
async def api_estadisticas(current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    return servicio.obtener_estadisticas_generales()

@router.get("/api/accesos/reporte-diario", response_model=ReporteDiario, name="API Reporte diario")
@rol_requerido_cookie("Superadministrador", "Administrador")
async def api_reporte_diario(fecha: Optional[str] = Query(None), current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    if fecha:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
    else:
        fecha_dt = datetime.now()
    
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    return servicio.generar_reporte_diario(fecha_dt)

@router.get("/api/accesos/reporte-semanal", name="API Reporte semanal")
@rol_requerido_cookie("Superadministrador", "Administrador")
async def api_reporte_semanal(fecha_inicio: Optional[str] = Query(None), current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    fecha_inicio_dt = None
    if fecha_inicio:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    return JSONResponse(servicio.generar_reporte_semanal(fecha_inicio_dt))

@router.get("/api/usuario/{usuario_id}/estado", name="API Estado del usuario")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante")
async def api_estado_usuario(usuario_id: str, current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    usuario = repo_usuarios.obtener_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    resumen = servicio.obtener_resumen_usuario(usuario_id)
    return JSONResponse(resumen)

@router.get("/api/usuario/{usuario_id}/accesos", response_model=List[AccesoRead], name="API Accesos de usuario")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante")
async def api_accesos_usuario(usuario_id: str, dias: int = Query(30, description="Días hacia atrás"), current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    if current_user_id != usuario_id:
        current_user = repo_usuarios.obtener_por_id(current_user_id)
        if not current_user or current_user.rol.value not in ["Superadministrador", "Administrador", "Vigilante"]:
            raise HTTPException(status_code=403, detail="No autorizado")
    
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    accesos = servicio.obtener_accesos_usuario(usuario_id, dias)
    return [AccesoRead.from_domain(acceso) for acceso in accesos]

@router.get("/api/accesos/buscar", response_model=List[AccesoRead], name="API Buscar accesos")
@rol_requerido_cookie("Superadministrador", "Administrador")
async def api_buscar_accesos(fecha_inicio: str = Query(...), fecha_fin: str = Query(...), usuario_id: Optional[str] = Query(None), tipo_movimiento: Optional[str] = Query(None), current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    try:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido")
    
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    accesos = servicio.obtener_accesos_periodo(fecha_inicio_dt, fecha_fin_dt)
    
    if usuario_id:
        accesos = [a for a in accesos if a.usuario.numero_documento.valor == usuario_id]
    
    if tipo_movimiento:
        accesos = [a for a in accesos if a.tipo_movimiento == tipo_movimiento]
    
    return [AccesoRead.from_domain(acceso) for acceso in accesos]

@router.get("/api/accesos/exportar-csv", name="API Exportar accesos CSV")
@rol_requerido_cookie("Superadministrador", "Administrador")
async def api_exportar_csv(fecha_inicio: str = Query(...), fecha_fin: str = Query(...), usuario_id: Optional[str] = Query(None), current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    try:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido")
    
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    csv_content = servicio.exportar_accesos_csv(fecha_inicio_dt, fecha_fin_dt, usuario_id)
    filename = f"accesos_{fecha_inicio}_{fecha_fin}.csv"
    
    return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})

@router.post("/api/limpiar-qr-expirados", name="API Limpiar QR expirados")
@rol_requerido_cookie("Superadministrador", "Administrador")
async def api_limpiar_qr_expirados(current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    eliminados = servicio.limpiar_qr_expirados()
    return JSONResponse({"success": True, "qr_eliminados": eliminados, "mensaje": f"Se eliminaron {eliminados} códigos QR expirados"})

@router.get("/api/dashboard-data", name="API Datos completos del dashboard")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante")
async def api_dashboard_data(current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    dashboard_data = servicio.obtener_dashboard_data()
    return JSONResponse(dashboard_data)

@router.get("/api/personas-dentro", name="API Personas actualmente dentro")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante")
async def api_personas_dentro(current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    personas_dentro = servicio.obtener_personas_dentro_ahora()
    return JSONResponse({"total": len(personas_dentro), "personas": personas_dentro})

@router.get("/api/accesos-recientes", name="API Accesos recientes")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante")
async def api_accesos_recientes(minutos: int = Query(30, description="Minutos hacia atrás"), current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    servicio = ServicioQRControl(repo_accesos, repo_usuarios)
    accesos_recientes = servicio.obtener_accesos_recientes(minutos)
    return JSONResponse(accesos_recientes)

@router.post("/api/usuario/{usuario_id}/qr/generar", response_model=QRTemporalResponse, name="API Generar QR temporal")
@rol_requerido_cookie("Superadministrador", "Administrador", "Aprendiz", "Funcionario", "Contratista", "Instructor")
async def api_generar_qr_temporal(usuario_id: str, qr_data: QRTemporalCreate, current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    if current_user_id != usuario_id:
        current_user = repo_usuarios.obtener_por_id(current_user_id)
        if not current_user or current_user.rol.value not in ["Superadministrador", "Administrador"]:
            raise HTTPException(status_code=403, detail="No autorizado")
    
    try:
        servicio = ServicioQRControl(repo_accesos, repo_usuarios)
        qr_temporal, imagen_base64 = servicio.generar_qr_usuario(usuario_id, qr_data.duracion_minutos)
        return QRTemporalResponse(qr_data=QRTemporalRead.from_domain(qr_temporal), qr_image=imagen_base64)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/vigilante/validar-qr", response_model=ValidacionQRResponse, name="API Validar QR")
@rol_requerido_cookie("Superadministrador", "Administrador", "Vigilante")
async def api_validar_qr(codigo_qr: str, current_user_id: str = Depends(validar_token_cookie), db: Session = Depends(get_db)):
    repo_usuarios = RepositorioUsuariosBD(db)
    repo_accesos = RepositorioAccesosBD(db, repo_usuarios)
    
    try:
        servicio = ServicioQRControl(repo_accesos, repo_usuarios)
        info = await servicio.validar_qr_codigo(codigo_qr)
        return ValidacionQRResponse(valido=True, mensaje=f"QR válido para {info['nombre_completo']}", **info)
    except ValueError as e:
        return ValidacionQRResponse(valido=False, mensaje=str(e))