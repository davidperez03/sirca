from datetime import datetime, timedelta
from app.modules.qr_control.domain.entidades.qr_temporal import QRTemporal
from app.modules.qr_control.domain.objetos_de_valor.codigo_qr import CodigoQR
from app.modules.qr_control.domain.puertos.repositorio_accesos import RepositorioAccesos
from app.modules.qr_control.infrastructure.servicios.generador_qr import GeneradorQR
from app.modules.autenticacion.domain.entidades.usuario import Usuario

class GenerarQRTemporal:
    def __init__(self, repositorio: RepositorioAccesos):
        self.repositorio = repositorio
        self.generador_qr = GeneradorQR()

    def ejecutar(self, usuario: Usuario, duracion_minutos: int = 5) -> tuple[QRTemporal, str]:
        """
        Genera un QR temporal para acceso único del usuario.
        Retorna tanto la entidad QRTemporal como la imagen base64.
        """
        # 1. Limpiar QRs anteriores del usuario que no han sido usados
        self._limpiar_qr_anteriores(usuario.numero_documento.valor)
        
        # 2. Generar código QR único
        codigo_qr = CodigoQR.generar_nuevo(usuario.numero_documento.valor)
        
        # 3. Crear QR temporal
        fecha_generacion = datetime.now()
        fecha_expiracion = fecha_generacion + timedelta(minutes=duracion_minutos)
        
        qr_temporal = QRTemporal(
            usuario_id=usuario.numero_documento.valor,
            codigo_qr=codigo_qr.valor,
            fecha_generacion=fecha_generacion,
            fecha_expiracion=fecha_expiracion,
            usado=False
        )
        
        # 4. Guardar en repositorio
        self.repositorio.guardar_qr_temporal(qr_temporal)
        
        # 5. Generar imagen QR
        imagen_base64 = self.generador_qr.generar_qr_imagen(codigo_qr.valor)
        
        return qr_temporal, imagen_base64

    def _limpiar_qr_anteriores(self, usuario_id: str):
        """Limpia QRs anteriores no usados del mismo usuario."""
        # Esta lógica ya está implementada en el repositorio
        pass

    def obtener_qr_activo(self, usuario_id: str) -> tuple[QRTemporal, str] | None:
        """
        Obtiene el QR activo del usuario si existe.
        """
        from sqlalchemy import and_
        # Necesitarías implementar un método en el repositorio para esto
        # Por ahora, retornamos None
        return None