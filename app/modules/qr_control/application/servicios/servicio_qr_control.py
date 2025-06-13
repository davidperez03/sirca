"""
Servicio principal para QR Control
Orquesta todos los casos de uso y proporciona una interfaz unificada
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from app.modules.qr_control.domain.puertos.repositorio_accesos import RepositorioAccesos
from app.modules.autenticacion.domain.puertos.repositorio_usuarios import RepositorioUsuarios
from app.modules.qr_control.application.casos_de_uso.generar_qr_temporal import GenerarQRTemporal
from app.modules.qr_control.application.casos_de_uso.procesar_acceso_qr import ProcesarAccesoQR
from app.modules.qr_control.application.casos_de_uso.consultar_accesos import ConsultarAccesos
from app.modules.qr_control.domain.entidades.registro_acceso import RegistroAcceso
from app.modules.qr_control.domain.entidades.qr_temporal import QRTemporal
from app.modules.autenticacion.domain.entidades.usuario import Usuario

class ServicioQRControl:
    """
    Servicio principal que orquesta todas las operaciones de QR Control
    """
    
    def __init__(self, repo_accesos: RepositorioAccesos, repo_usuarios: RepositorioUsuarios):
        self.repo_accesos = repo_accesos
        self.repo_usuarios = repo_usuarios
        self.generar_qr = GenerarQRTemporal(repo_accesos)
        self.procesar_acceso = ProcesarAccesoQR(repo_accesos, repo_usuarios)
        self.consultar_accesos = ConsultarAccesos(repo_accesos)

    # ==================== OPERACIONES DE QR TEMPORAL ====================
    
    def generar_qr_usuario(self, usuario_id: str, duracion_minutos: int = 5) -> Tuple[QRTemporal, str]:
        """
        Genera un QR temporal para un usuario específico.
        
        Args:
            usuario_id: ID del usuario
            duracion_minutos: Duración del QR en minutos (1-60)
            
        Returns:
            Tuple con la entidad QRTemporal y la imagen base64
            
        Raises:
            ValueError: Si el usuario no existe, está inactivo o duración inválida
        """
        # Validar usuario
        usuario = self.repo_usuarios.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        if not usuario.activo:
            raise ValueError("Usuario inactivo")
        
        # Validar duración
        if not 1 <= duracion_minutos <= 60:
            raise ValueError("La duración debe estar entre 1 y 60 minutos")
        
        return self.generar_qr.ejecutar(usuario, duracion_minutos)
    
    def obtener_qr_activo_usuario(self, usuario_id: str) -> Optional[QRTemporal]:
        """
        Obtiene el QR activo (no usado y no expirado) de un usuario.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            QRTemporal si existe uno activo, None en caso contrario
        """
        # Implementar lógica para obtener QR activo
        # Esto requeriría un método adicional en el repositorio
        return None
    
    # ==================== OPERACIONES DE ACCESO ====================
    
    async def validar_qr_codigo(self, codigo_qr: str) -> dict:
        """
        Valida un código QR sin procesarlo.
        
        Args:
            codigo_qr: Código QR a validar
            
        Returns:
            Diccionario con información del usuario y validación
            
        Raises:
            ValueError: Si el QR no es válido
        """
        return self.procesar_acceso.validar_qr_sin_procesar(codigo_qr)
    
    async def procesar_acceso_qr(
        self,
        codigo_qr: str,
        vigilante_id: str,
        ubicacion: str = "Entrada Principal",
        items_declarados: List[str] = None,
        observaciones: str = ""
    ) -> RegistroAcceso:
        """
        Procesa un acceso usando código QR.
        
        Args:
            codigo_qr: Código QR escaneado
            vigilante_id: ID del vigilante que procesa
            ubicacion: Ubicación del acceso
            items_declarados: Lista de items declarados
            observaciones: Observaciones adicionales
            
        Returns:
            RegistroAcceso creado
            
        Raises:
            ValueError: Si hay errores en la validación o procesamiento
        """
        return await self.procesar_acceso.ejecutar(
            codigo_qr=codigo_qr,
            vigilante_id=vigilante_id,
            ubicacion=ubicacion,
            items_declarados=items_declarados or [],
            observaciones=observaciones
        )
    
    def obtener_estado_usuario(self, usuario_id: str) -> str:
        """
        Obtiene el estado actual de un usuario (DENTRO/FUERA/BLOQUEADO).
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Estado actual del usuario
        """
        return self.consultar_accesos.obtener_estado_actual_usuario(usuario_id)
    
    def obtener_ultimo_acceso_usuario(self, usuario_id: str) -> Optional[RegistroAcceso]:
        """
        Obtiene el último acceso registrado de un usuario.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            RegistroAcceso o None si no tiene accesos
        """
        return self.consultar_accesos.obtener_ultimo_acceso_usuario(usuario_id)
    
    # ==================== CONSULTAS Y REPORTES ====================
    
    def obtener_accesos_usuario(
        self,
        usuario_id: str,
        dias_atras: int = 30
    ) -> List[RegistroAcceso]:
        """
        Obtiene el historial de accesos de un usuario.
        
        Args:
            usuario_id: ID del usuario
            dias_atras: Días hacia atrás para consultar
            
        Returns:
            Lista de registros de acceso
        """
        fecha_fin = datetime.now()
        fecha_inicio = fecha_fin - timedelta(days=dias_atras)
        
        return self.consultar_accesos.obtener_accesos_usuario(
            usuario_id, fecha_inicio, fecha_fin
        )
    
    def obtener_accesos_hoy(self) -> List[RegistroAcceso]:
        """
        Obtiene todos los accesos del día actual.
        
        Returns:
            Lista de accesos de hoy
        """
        return self.consultar_accesos.obtener_accesos_hoy()
    
    def obtener_accesos_periodo(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ) -> List[RegistroAcceso]:
        """
        Obtiene accesos en un período específico.
        
        Args:
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
            
        Returns:
            Lista de accesos en el período
        """
        return self.consultar_accesos.obtener_accesos_por_periodo(fecha_inicio, fecha_fin)
    
    def generar_reporte_diario(self, fecha: Optional[datetime] = None) -> dict:
        """
        Genera un reporte completo de accesos del día.
        
        Args:
            fecha: Fecha del reporte (hoy por defecto)
            
        Returns:
            Diccionario con estadísticas y detalles
        """
        return self.consultar_accesos.generar_reporte_diario(fecha)
    
    def obtener_estadisticas_generales(self) -> dict:
        """
        Obtiene estadísticas generales del sistema.
        
        Returns:
            Diccionario con estadísticas
        """
        return self.consultar_accesos.obtener_estadisticas_generales()
    
    def obtener_accesos_recientes(self, minutos: int = 30) -> List[dict]:
        """
        Obtiene accesos recientes desde caché.
        
        Args:
            minutos: Minutos hacia atrás
            
        Returns:
            Lista de accesos recientes
        """
        return self.consultar_accesos.obtener_accesos_recientes(minutos)
    
    # ==================== OPERACIONES DE MANTENIMIENTO ====================
    
    def limpiar_qr_expirados(self) -> int:
        """
        Limpia códigos QR expirados del sistema.
        
        Returns:
            Número de códigos QR eliminados
        """
        return self.consultar_accesos.limpiar_qr_expirados()
    
    def obtener_personas_dentro_ahora(self) -> List[dict]:
        """
        Obtiene lista de personas que están actualmente dentro.
        
        Returns:
            Lista con información de personas dentro
        """
        accesos_hoy = self.obtener_accesos_hoy()
        
        # Agrupar por usuario y obtener último movimiento
        usuarios_estado = {}
        for acceso in sorted(accesos_hoy, key=lambda x: x.fecha_hora):
            usuario_id = acceso.usuario.numero_documento.valor
            usuarios_estado[usuario_id] = {
                'usuario': acceso.usuario,
                'ultimo_movimiento': acceso.tipo_movimiento,
                'fecha_hora': acceso.fecha_hora
            }
        
        # Filtrar solo los que están dentro
        personas_dentro = []
        for user_id, info in usuarios_estado.items():
            if info['ultimo_movimiento'] == 'INGRESO':
                personas_dentro.append({
                    'usuario_id': user_id,
                    'nombre': f"{info['usuario'].nombres.valor} {info['usuario'].apellidos.valor}",
                    'rol': info['usuario'].rol.value,
                    'hora_ingreso': info['fecha_hora'],
                    'tiempo_dentro': int((datetime.now() - info['fecha_hora']).total_seconds() / 60)
                })
        
        return personas_dentro
    
    def obtener_dashboard_data(self) -> dict:
        """
        Obtiene todos los datos necesarios para el dashboard.
        
        Returns:
            Diccionario con datos completos del dashboard
        """
        estadisticas = self.obtener_estadisticas_generales()
        accesos_recientes = self.obtener_accesos_recientes(30)
        personas_dentro = self.obtener_personas_dentro_ahora()
        
        # Generar alertas
        alertas = []
        
        # Alerta si hay muchas personas dentro
        if len(personas_dentro) > 50:
            alertas.append(f"Alto número de personas dentro: {len(personas_dentro)}")
        
        # Alerta si alguien lleva mucho tiempo dentro
        for persona in personas_dentro:
            if persona['tiempo_dentro'] > 480:  # 8 horas
                alertas.append(f"{persona['nombre']} lleva {persona['tiempo_dentro']//60} horas dentro")
        
        return {
            'estadisticas': estadisticas,
            'accesos_recientes': accesos_recientes,
            'personas_dentro': len(personas_dentro),
            'personas_dentro_lista': personas_dentro,
            'alertas': alertas
        }
    
    # ==================== VALIDACIONES DE NEGOCIO ====================
    
    def validar_permisos_usuario(self, usuario_solicitante_id: str, usuario_objetivo_id: str) -> bool:
        """
        Valida si un usuario tiene permisos para acceder a información de otro usuario.
        
        Args:
            usuario_solicitante_id: ID del usuario que solicita
            usuario_objetivo_id: ID del usuario objetivo
            
        Returns:
            True si tiene permisos, False en caso contrario
        """
        # El usuario puede ver su propia información
        if usuario_solicitante_id == usuario_objetivo_id:
            return True
        
        # Administradores pueden ver información de cualquier usuario
        usuario_solicitante = self.repo_usuarios.obtener_por_id(usuario_solicitante_id)
        if usuario_solicitante and usuario_solicitante.rol.value in ["Superadministrador", "Administrador"]:
            return True
        
        return False
    
    def validar_permisos_vigilante(self, usuario_id: str) -> bool:
        """
        Valida si un usuario tiene permisos de vigilante.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            True si tiene permisos de vigilante, False en caso contrario
        """
        usuario = self.repo_usuarios.obtener_por_id(usuario_id)
        if not usuario:
            return False
        
        return usuario.rol.value in ["Superadministrador", "Administrador", "Vigilante"]
    
    def validar_permisos_admin(self, usuario_id: str) -> bool:
        """
        Valida si un usuario tiene permisos de administrador.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            True si tiene permisos de admin, False en caso contrario
        """
        usuario = self.repo_usuarios.obtener_por_id(usuario_id)
        if not usuario:
            return False
        
        return usuario.rol.value in ["Superadministrador", "Administrador"]
    
    # ==================== MÉTODOS DE UTILIDAD ====================
    
    def obtener_resumen_usuario(self, usuario_id: str) -> dict:
        """
        Obtiene un resumen completo de la actividad de un usuario.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Diccionario con resumen completo
        """
        usuario = self.repo_usuarios.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        estado_actual = self.obtener_estado_usuario(usuario_id)
        ultimo_acceso = self.obtener_ultimo_acceso_usuario(usuario_id)
        accesos_mes = self.obtener_accesos_usuario(usuario_id, 30)
        accesos_hoy = [a for a in accesos_mes 
                      if a.fecha_hora.date() == datetime.now().date()]
        
        # Calcular estadísticas
        total_ingresos = len([a for a in accesos_mes if a.tipo_movimiento == "INGRESO"])
        total_salidas = len([a for a in accesos_mes if a.tipo_movimiento == "SALIDA"])
        
        # Calcular tiempo promedio dentro (solo días completos)
        tiempos_dentro = []
        accesos_ordenados = sorted(accesos_mes, key=lambda x: x.fecha_hora)
        
        ingreso_temp = None
        for acceso in accesos_ordenados:
            if acceso.tipo_movimiento == "INGRESO":
                ingreso_temp = acceso.fecha_hora
            elif acceso.tipo_movimiento == "SALIDA" and ingreso_temp:
                tiempo_dentro = (acceso.fecha_hora - ingreso_temp).total_seconds() / 3600  # horas
                tiempos_dentro.append(tiempo_dentro)
                ingreso_temp = None
        
        tiempo_promedio = sum(tiempos_dentro) / len(tiempos_dentro) if tiempos_dentro else 0
        
        return {
            'usuario': {
                'id': usuario.numero_documento.valor,
                'nombre_completo': f"{usuario.nombres.valor} {usuario.apellidos.valor}",
                'rol': usuario.rol.value,
                'activo': usuario.activo
            },
            'estado_actual': estado_actual,
            'ultimo_acceso': ultimo_acceso,
            'estadisticas': {
                'accesos_mes': len(accesos_mes),
                'accesos_hoy': len(accesos_hoy),
                'ingresos_mes': total_ingresos,
                'salidas_mes': total_salidas,
                'tiempo_promedio_horas': round(tiempo_promedio, 2),
                'dias_activos': len(set(a.fecha_hora.date() for a in accesos_mes))
            }
        }
    
    def buscar_usuarios_por_acceso(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        tipo_movimiento: Optional[str] = None
    ) -> List[dict]:
        """
        Busca usuarios que tuvieron accesos en un período específico.
        
        Args:
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
            tipo_movimiento: Filtro por tipo (INGRESO/SALIDA)
            
        Returns:
            Lista de usuarios con información de accesos
        """
        accesos = self.obtener_accesos_periodo(fecha_inicio, fecha_fin)
        
        if tipo_movimiento:
            accesos = [a for a in accesos if a.tipo_movimiento == tipo_movimiento]
        
        # Agrupar por usuario
        usuarios_accesos = {}
        for acceso in accesos:
            user_id = acceso.usuario.numero_documento.valor
            if user_id not in usuarios_accesos:
                usuarios_accesos[user_id] = {
                    'usuario': acceso.usuario,
                    'accesos': []
                }
            usuarios_accesos[user_id]['accesos'].append(acceso)
        
        # Formatear resultado
        resultado = []
        for user_id, data in usuarios_accesos.items():
            usuario = data['usuario']
            accesos_usuario = data['accesos']
            
            resultado.append({
                'usuario_id': user_id,
                'nombre_completo': f"{usuario.nombres.valor} {usuario.apellidos.valor}",
                'rol': usuario.rol.value,
                'total_accesos': len(accesos_usuario),
                'primer_acceso': min(accesos_usuario, key=lambda x: x.fecha_hora).fecha_hora,
                'ultimo_acceso': max(accesos_usuario, key=lambda x: x.fecha_hora).fecha_hora,
                'tipos_movimiento': list(set(a.tipo_movimiento for a in accesos_usuario))
            })
        
        return sorted(resultado, key=lambda x: x['total_accesos'], reverse=True)
    
    def generar_reporte_semanal(self, fecha_inicio: Optional[datetime] = None) -> dict:
        """
        Genera un reporte semanal de actividad.
        
        Args:
            fecha_inicio: Fecha de inicio de la semana (lunes actual por defecto)
            
        Returns:
            Diccionario con reporte semanal
        """
        if not fecha_inicio:
            hoy = datetime.now()
            dias_desde_lunes = hoy.weekday()
            fecha_inicio = hoy - timedelta(days=dias_desde_lunes)
            fecha_inicio = fecha_inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        
        fecha_fin = fecha_inicio + timedelta(days=7)
        
        # Obtener accesos de la semana
        accesos_semana = self.obtener_accesos_periodo(fecha_inicio, fecha_fin)
        
        # Estadísticas por día
        accesos_por_dia = {}
        for i in range(7):
            fecha_dia = fecha_inicio + timedelta(days=i)
            dia_nombre = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][i]
            accesos_dia = [a for a in accesos_semana if a.fecha_hora.date() == fecha_dia.date()]
            
            accesos_por_dia[dia_nombre] = {
                'fecha': fecha_dia.date(),
                'total_accesos': len(accesos_dia),
                'ingresos': len([a for a in accesos_dia if a.tipo_movimiento == "INGRESO"]),
                'salidas': len([a for a in accesos_dia if a.tipo_movimiento == "SALIDA"]),
                'usuarios_unicos': len(set(a.usuario.numero_documento.valor for a in accesos_dia))
            }
        
        # Top usuarios más activos
        usuarios_actividad = {}
        for acceso in accesos_semana:
            user_id = acceso.usuario.numero_documento.valor
            if user_id not in usuarios_actividad:
                usuarios_actividad[user_id] = {
                    'usuario': acceso.usuario,
                    'accesos': 0
                }
            usuarios_actividad[user_id]['accesos'] += 1
        
        top_usuarios = sorted(
            usuarios_actividad.values(),
            key=lambda x: x['accesos'],
            reverse=True
        )[:10]
        
        return {
            'periodo': {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            },
            'resumen': {
                'total_accesos': len(accesos_semana),
                'usuarios_unicos': len(set(a.usuario.numero_documento.valor for a in accesos_semana)),
                'promedio_accesos_dia': len(accesos_semana) / 7,
                'dia_mas_activo': max(accesos_por_dia.items(), key=lambda x: x[1]['total_accesos'])[0]
            },
            'accesos_por_dia': accesos_por_dia,
            'top_usuarios': [
                {
                    'nombre': f"{u['usuario'].nombres.valor} {u['usuario'].apellidos.valor}",
                    'usuario_id': u['usuario'].numero_documento.valor,
                    'rol': u['usuario'].rol.value,
                    'accesos': u['accesos']
                }
                for u in top_usuarios
            ]
        }
    
    # ==================== MÉTODOS DE EXPORTACIÓN ====================
    
    def exportar_accesos_csv(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        usuario_id: Optional[str] = None
    ) -> str:
        """
        Exporta accesos a formato CSV.
        
        Args:
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
            usuario_id: Filtrar por usuario específico
            
        Returns:
            String con contenido CSV
        """
        accesos = self.obtener_accesos_periodo(fecha_inicio, fecha_fin)
        
        if usuario_id:
            accesos = [a for a in accesos if a.usuario.numero_documento.valor == usuario_id]
        
        # Crear CSV
        csv_lines = [
            "Fecha,Hora,Usuario,Documento,Rol,Tipo_Movimiento,Vigilante,Ubicacion,Items_Declarados,Observaciones"
        ]
        
        for acceso in accesos:
            items = ";".join(acceso.items_declarados) if acceso.items_declarados else ""
            observaciones = acceso.observaciones.replace(',', ';').replace('\n', ' ')
            
            csv_lines.append(
                f"{acceso.fecha_hora.strftime('%Y-%m-%d')},"
                f"{acceso.fecha_hora.strftime('%H:%M:%S')},"
                f"\"{acceso.usuario.nombres.valor} {acceso.usuario.apellidos.valor}\","
                f"{acceso.usuario.numero_documento.valor},"
                f"{acceso.usuario.rol.value},"
                f"{acceso.tipo_movimiento},"
                f"{acceso.vigilante_id},"
                f"{acceso.ubicacion},"
                f"\"{items}\","
                f"\"{observaciones}\""
            )
        
        return "\n".join(csv_lines)