from datetime import datetime
from typing import List
from app.modules.qr_control.domain.entidades.registro_acceso import RegistroAcceso
from app.modules.qr_control.domain.objetos_de_valor.estado_acceso import EstadoAcceso
from app.modules.qr_control.domain.objetos_de_valor.tipo_movimiento import TipoMovimiento
from app.modules.qr_control.domain.puertos.repositorio_accesos import RepositorioAccesos
from app.modules.qr_control.infrastructure.servicios.notificador_accesos import NotificadorAccesos
from app.modules.autenticacion.domain.puertos.repositorio_usuarios import RepositorioUsuarios

class ProcesarAccesoQR:
    def __init__(self, repositorio_accesos: RepositorioAccesos, repositorio_usuarios: RepositorioUsuarios):
        self.repositorio_accesos = repositorio_accesos
        self.repositorio_usuarios = repositorio_usuarios
        self.notificador = NotificadorAccesos()

    async def ejecutar(
        self,
        codigo_qr: str,
        vigilante_id: str,
        ubicacion: str = "Entrada Principal",
        items_declarados: List[str] = None,
        observaciones: str = ""
    ) -> RegistroAcceso:
        """
        Procesa el acceso usando un código QR.
        """
        if items_declarados is None:
            items_declarados = []

        # 1. Validar QR temporal
        qr_temporal = self.repositorio_accesos.obtener_qr_temporal(codigo_qr)
        if not qr_temporal:
            raise ValueError("Código QR no válido o no encontrado")

        if qr_temporal.usado:
            raise ValueError("Este código QR ya fue utilizado")

        if qr_temporal.fecha_expiracion < datetime.now():
            raise ValueError("El código QR ha expirado")

        # 2. Obtener usuario
        usuario = self.repositorio_usuarios.obtener_por_id(qr_temporal.usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado")

        if not usuario.activo:
            raise ValueError("Usuario inactivo")

        # 3. Determinar tipo de movimiento
        estado_actual = self.repositorio_accesos.obtener_estado_usuario(qr_temporal.usuario_id)
        
        if estado_actual == EstadoAcceso.FUERA:
            tipo_movimiento = TipoMovimiento.INGRESO
        elif estado_actual == EstadoAcceso.DENTRO:
            tipo_movimiento = TipoMovimiento.SALIDA
        else:  # BLOQUEADO
            raise ValueError("Usuario bloqueado. Contacte al administrador")

        # 4. Registrar acceso
        registro = RegistroAcceso(
            usuario=usuario,
            tipo_movimiento=tipo_movimiento.value,
            fecha_hora=datetime.now(),
            vigilante_id=vigilante_id,
            ubicacion=ubicacion,
            items_declarados=items_declarados,
            observaciones=observaciones
        )

        self.repositorio_accesos.guardar_registro(registro)

        # 5. Marcar QR como usado
        self.repositorio_accesos.marcar_qr_usado(codigo_qr, vigilante_id)

        # 6. Notificar en tiempo real
        await self.notificador.notificar_acceso_tiempo_real(registro)

        return registro

    def validar_qr_sin_procesar(self, codigo_qr: str) -> dict:
        """
        Valida un QR sin procesarlo, retorna información del usuario.
        """
        qr_temporal = self.repositorio_accesos.obtener_qr_temporal(codigo_qr)
        if not qr_temporal:
            raise ValueError("Código QR no válido o no encontrado")

        if qr_temporal.usado:
            raise ValueError("Este código QR ya fue utilizado")

        if qr_temporal.fecha_expiracion < datetime.now():
            raise ValueError("El código QR ha expirado")

        usuario = self.repositorio_usuarios.obtener_por_id(qr_temporal.usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado")

        estado_actual = self.repositorio_accesos.obtener_estado_usuario(qr_temporal.usuario_id)
        tipo_siguiente = TipoMovimiento.INGRESO if estado_actual == EstadoAcceso.FUERA else TipoMovimiento.SALIDA

        return {
            "usuario_id": usuario.numero_documento.valor,
            "nombre_completo": f"{usuario.nombres.valor} {usuario.apellidos.valor}",
            "rol": usuario.rol.value,
            "estado_actual": estado_actual,
            "tipo_siguiente": tipo_siguiente.value,
            "expira_en": int((qr_temporal.fecha_expiracion - datetime.now()).total_seconds()),
            "valido": True
        }