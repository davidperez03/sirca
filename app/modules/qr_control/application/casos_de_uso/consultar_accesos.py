from datetime import datetime, timedelta
from typing import List, Optional
from app.modules.qr_control.domain.entidades.registro_acceso import RegistroAcceso
from app.modules.qr_control.domain.puertos.repositorio_accesos import RepositorioAccesos
from app.modules.qr_control.infrastructure.servicios.notificador_accesos import NotificadorAccesos

class ConsultarAccesos:
    def __init__(self, repositorio: RepositorioAccesos):
        self.repositorio = repositorio
        self.notificador = NotificadorAccesos()

    def obtener_accesos_por_periodo(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ) -> List[RegistroAcceso]:
        """Obtiene registros de acceso en un período específico."""
        return self.repositorio.listar_accesos_por_fecha(fecha_inicio, fecha_fin)

    def obtener_accesos_hoy(self) -> List[RegistroAcceso]:
        """Obtiene todos los accesos del día actual."""
        hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        mañana = hoy + timedelta(days=1)
        return self.obtener_accesos_por_periodo(hoy, mañana)

    def obtener_accesos_usuario(
        self,
        usuario_id: str,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None
    ) -> List[RegistroAcceso]:
        """Obtiene accesos de un usuario específico."""
        if not fecha_inicio:
            fecha_inicio = datetime.now() - timedelta(days=30)  # Último mes por defecto
        if not fecha_fin:
            fecha_fin = datetime.now()

        todos_los_accesos = self.repositorio.listar_accesos_por_fecha(fecha_inicio, fecha_fin)
        return [acceso for acceso in todos_los_accesos 
                if acceso.usuario.numero_documento.valor == usuario_id]

    def obtener_ultimo_acceso_usuario(self, usuario_id: str) -> Optional[RegistroAcceso]:
        """Obtiene el último acceso registrado de un usuario."""
        return self.repositorio.obtener_ultimo_acceso(usuario_id)

    def obtener_estado_actual_usuario(self, usuario_id: str) -> str:
        """Obtiene el estado actual de un usuario (DENTRO/FUERA/BLOQUEADO)."""
        return self.repositorio.obtener_estado_usuario(usuario_id)

    def obtener_accesos_recientes(self, minutos: int = 30) -> List[dict]:
        """Obtiene accesos recientes desde caché."""
        return self.notificador.obtener_accesos_recientes(minutos)

    def generar_reporte_diario(self, fecha: Optional[datetime] = None) -> dict:
        """Genera un reporte de accesos del día."""
        if not fecha:
            fecha = datetime.now()

        inicio_dia = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
        fin_dia = inicio_dia + timedelta(days=1)

        accesos = self.obtener_accesos_por_periodo(inicio_dia, fin_dia)

        # Estadísticas
        total_accesos = len(accesos)
        ingresos = len([a for a in accesos if a.tipo_movimiento == "INGRESO"])
        salidas = len([a for a in accesos if a.tipo_movimiento == "SALIDA"])

        # Personas actualmente dentro
        usuarios_unicos = set()
        estado_usuarios = {}
        
        for acceso in sorted(accesos, key=lambda x: x.fecha_hora):
            usuario_id = acceso.usuario.numero_documento.valor
            usuarios_unicos.add(usuario_id)
            estado_usuarios[usuario_id] = acceso.tipo_movimiento

        dentro_ahora = len([uid for uid, estado in estado_usuarios.items() 
                           if estado == "INGRESO"])

        # Accesos por hora
        accesos_por_hora = {}
        for acceso in accesos:
            hora = acceso.fecha_hora.hour
            if hora not in accesos_por_hora:
                accesos_por_hora[hora] = 0
            accesos_por_hora[hora] += 1

        return {
            "fecha": fecha.strftime("%Y-%m-%d"),
            "total_accesos": total_accesos,
            "ingresos": ingresos,
            "salidas": salidas,
            "usuarios_unicos": len(usuarios_unicos),
            "dentro_actualmente": dentro_ahora,
            "accesos_por_hora": accesos_por_hora,
            "accesos_detalle": accesos
        }

    def limpiar_qr_expirados(self) -> int:
        """Limpia códigos QR expirados."""
        return self.repositorio.limpiar_qr_expirados()

    def obtener_estadisticas_generales(self) -> dict:
        """Obtiene estadísticas generales del sistema."""
        hoy = datetime.now()
        inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        accesos_mes = self.obtener_accesos_por_periodo(inicio_mes, hoy)
        accesos_hoy = self.obtener_accesos_hoy()

        return {
            "accesos_hoy": len(accesos_hoy),
            "accesos_mes": len(accesos_mes),
            "ingresos_hoy": len([a for a in accesos_hoy if a.tipo_movimiento == "INGRESO"]),
            "salidas_hoy": len([a for a in accesos_hoy if a.tipo_movimiento == "SALIDA"]),
            "qr_expirados_limpiados": self.limpiar_qr_expirados()
        }