'''
Caso de uso para generar QR de acceso para un usuario
'''
from datetime import datetime, timedelta
from typing import List, Tuple
from app.modules.qr_acceso.domain.entidades.qr_acceso import QRAcceso
from app.modules.qr_acceso.domain.objetos_de_valor.qr_jwt import QRJwt
from app.modules.qr_acceso.domain.objetos_de_valor.estado_usuario import EstadoUsuario
from app.modules.qr_acceso.domain.puertos.repositorio_qr_acceso import RepositorioQRAcceso
from app.modules.autenticacion.domain.entidades.usuario import Usuario
from app.modules.pertenencias.domain.puertos.repositorio_pertenencias import RepositorioPertenencias
from app.modules.vehiculos.domain.puertos.repositorio_vehiculos import RepositorioVehiculos

class GenerarQRUsuario:
    def __init__(
        self, 
        repo_qr: RepositorioQRAcceso,
        repo_pertenencias: RepositorioPertenencias = None,
        repo_vehiculos: RepositorioVehiculos = None
    ):
        self.repo_qr = repo_qr
        self.repo_pertenencias = repo_pertenencias
        self.repo_vehiculos = repo_vehiculos
    
    def ejecutar(
        self, 
        usuario: Usuario, 
        duracion_minutos: int = 15,
        incluir_pertenencias: bool = True,
        incluir_vehiculos: bool = True
    ) -> Tuple[QRAcceso, str]:
        """
        Genera un QR de acceso para el usuario.
        Retorna: (QRAcceso, imagen_base64)
        """
        
        # 1. Validaciones
        if not usuario.activo:
            raise ValueError("Usuario inactivo no puede generar QR")
        
        if not 1 <= duracion_minutos <= 60:
            raise ValueError("Duración debe estar entre 1 y 60 minutos")
        
        # 2. Verificar estado del usuario
        estado_actual = self._obtener_estado_usuario(usuario.numero_documento.valor)
        if not estado_actual.puede_generar_qr():
            raise ValueError("Usuario bloqueado no puede generar QR")
        
        # 3. Limpiar QRs anteriores no usados del usuario
        self._limpiar_qrs_anteriores(usuario.numero_documento.valor)
        
        # 4. Obtener pertenencias y vehículos activos
        pertenencias_incluidas = []
        vehiculos_incluidos = []
        
        if incluir_pertenencias and self.repo_pertenencias:
            pertenencias_incluidas = self._obtener_pertenencias_activas(usuario.numero_documento.valor)
        
        if incluir_vehiculos and self.repo_vehiculos:
            vehiculos_incluidos = self._obtener_vehiculos_activos(usuario.numero_documento.valor)
        
        # 5. Crear JWT para el QR
        qr_jwt = QRJwt.crear_nuevo(
            usuario_id=usuario.numero_documento.valor,
            duracion_minutos=duracion_minutos,
            pertenencias=pertenencias_incluidas,
            vehiculos=vehiculos_incluidos
        )
        
        # 6. Crear entidad QRAcceso
        fecha_generacion = datetime.now()
        fecha_expiracion = fecha_generacion + timedelta(minutes=duracion_minutos)
        
        qr_acceso = QRAcceso(
            usuario=usuario,
            token_jwt=qr_jwt.valor,
            fecha_generacion=fecha_generacion,
            fecha_expiracion=fecha_expiracion,
            duracion_minutos=duracion_minutos,
            pertenencias_incluidas=pertenencias_incluidas,
            vehiculos_incluidos=vehiculos_incluidos,
            usado=False
        )
        
        # 7. Guardar en repositorio
        self.repo_qr.guardar_qr(qr_acceso)
        
        # 8. Generar imagen del QR
        imagen_base64 = self._generar_imagen_qr(qr_jwt.valor)
        
        return qr_acceso, imagen_base64
    
    def _obtener_estado_usuario(self, usuario_id: str) -> EstadoUsuario:
        """Obtiene el estado actual del usuario"""
        ultimo_registro = self.repo_qr.obtener_ultimo_registro_usuario(usuario_id)
        
        if not ultimo_registro:
            return EstadoUsuario.FUERA
        
        return EstadoUsuario.desde_ultimo_movimiento(ultimo_registro.tipo_movimiento)
    
    def _limpiar_qrs_anteriores(self, usuario_id: str):
        """Limpia QRs anteriores no usados del usuario"""
        # Los QRs antiguos se limpiarán automáticamente por expiración
        # o se puede implementar una lógica específica aquí
        pass
    
    def _obtener_pertenencias_activas(self, usuario_id: str) -> List[dict]:
        """Obtiene pertenencias activas del usuario"""
        if not self.repo_pertenencias:
            return []
        
        try:
            pertenencias = self.repo_pertenencias.listar_por_usuario(usuario_id, incluir_inactivos=False)
            return [
                {
                    "id": p.id,
                    "nombre": p.nombre.valor,
                    "tipo": p.tipo.value,
                    "serial": p.serial.valor if p.serial.valor else None
                }
                for p in pertenencias
            ]
        except Exception:
            return []
    
    def _obtener_vehiculos_activos(self, usuario_id: str) -> List[dict]:
        """Obtiene vehículos activos del usuario"""
        if not self.repo_vehiculos:
            return []
        
        try:
            vehiculos = self.repo_vehiculos.listar_por_usuario(usuario_id, incluir_inactivos=False)
            return [
                {
                    "placa": v.placa.valor,
                    "tipo": v.tipo.value,
                    "marca": v.marca.valor,
                    "modelo": v.modelo.valor,
                    "color": v.color.valor
                }
                for v in vehiculos
            ]
        except Exception:
            return []
    
    def _generar_imagen_qr(self, token_jwt: str) -> str:
        """Genera imagen base64 del QR"""
        import qrcode
        import io
        import base64
        from PIL import Image
        
        # Crear QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        
        qr.add_data(token_jwt)
        qr.make(fit=True)
        
        # Crear imagen
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"