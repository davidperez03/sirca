'''
Implementación del repositorio de QR Acceso para base de datos
'''
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from datetime import datetime, timedelta
from app.modules.qr_acceso.domain.puertos.repositorio_qr_acceso import RepositorioQRAcceso
from app.modules.qr_acceso.domain.entidades.qr_acceso import QRAcceso
from app.modules.qr_acceso.domain.entidades.registro_acceso import RegistroAcceso
from app.modules.qr_acceso.infrastructure.modelos.modelo_qr_acceso import QRAccesoORM, RegistroAccesoORM
from app.modules.autenticacion.domain.puertos.repositorio_usuarios import RepositorioUsuarios

class RepositorioQRAccesoBD(RepositorioQRAcceso):
    def __init__(self, session: Session, repo_usuarios: RepositorioUsuarios):
        self.session = session
        self.repo_usuarios = repo_usuarios
    
    # ========== MÉTODOS DE MAPEO ==========
    
    def _mapear_qr_a_dominio(self, orm: QRAccesoORM) -> QRAcceso:
        """Convierte un QRAccesoORM a entidad de dominio QRAcceso"""
        # Obtener usuario asociado
        usuario = self.repo_usuarios.obtener_por_id(orm.usuario_id)
        if not usuario:
            raise ValueError(f"Usuario {orm.usuario_id} no encontrado")
        
        return QRAcceso(
            id=orm.id,
            usuario=usuario,
            token_jwt=orm.token_jwt,
            fecha_generacion=orm.fecha_generacion,
            fecha_expiracion=orm.fecha_expiracion,
            duracion_minutos=orm.duracion_minutos,
            pertenencias_incluidas=orm.pertenencias_incluidas,
            vehiculos_incluidos=orm.vehiculos_incluidos,
            usado=orm.usado
        )
    
    def _mapear_registro_a_dominio(self, orm: RegistroAccesoORM) -> RegistroAcceso:
        """Convierte un RegistroAccesoORM a entidad de dominio RegistroAcceso"""
        # Obtener usuario asociado
        usuario = self.repo_usuarios.obtener_por_id(orm.usuario_id)
        if not usuario:
            raise ValueError(f"Usuario {orm.usuario_id} no encontrado")
        
        return RegistroAcceso(
            id=orm.id,
            usuario=usuario,
            tipo_movimiento=orm.tipo_movimiento,
            fecha_hora=orm.fecha_hora,
            vigilante_id=orm.vigilante_id,
            ubicacion=orm.ubicacion,
            pertenencias_declaradas=orm.pertenencias_declaradas or [],
            vehiculos_declarados=orm.vehiculos_declarados or [],
            observaciones=orm.observaciones,
            qr_usado_id=orm.qr_usado_id
        )
    
    # ========== OPERACIONES QR ==========
    
    def guardar_qr(self, qr_acceso: QRAcceso) -> None:
        """Guarda un QR de acceso temporal"""
        # Primero limpiar QRs anteriores no usados del usuario
        self.session.query(QRAccesoORM).filter(
            and_(
                QRAccesoORM.usuario_id == qr_acceso.usuario.numero_documento.valor,
                QRAccesoORM.usado == False
            )
        ).delete()
        
        # Crear nuevo QR
        orm = QRAccesoORM(
            usuario_id=qr_acceso.usuario.numero_documento.valor,
            token_jwt=qr_acceso.token_jwt,
            fecha_generacion=qr_acceso.fecha_generacion,
            fecha_expiracion=qr_acceso.fecha_expiracion,
            duracion_minutos=qr_acceso.duracion_minutos,
            pertenencias_incluidas=qr_acceso.pertenencias_incluidas,
            vehiculos_incluidos=qr_acceso.vehiculos_incluidos,
            usado=qr_acceso.usado
        )
        
        self.session.add(orm)
        self.session.commit()
        qr_acceso.id = orm.id
    
    def obtener_qr_por_jwt(self, token_jwt: str) -> Optional[QRAcceso]:
        """Obtiene un QR por su token JWT"""
        orm = self.session.query(QRAccesoORM).filter_by(token_jwt=token_jwt).first()
        if not orm:
            return None
        return self._mapear_qr_a_dominio(orm)
    
    def obtener_qrs_activos_usuario(self, usuario_id: str) -> List[QRAcceso]:
        """Obtiene QRs activos (no usados y no expirados) de un usuario"""
        ahora = datetime.now()
        orms = self.session.query(QRAccesoORM).filter(
            and_(
                QRAccesoORM.usuario_id == usuario_id,
                QRAccesoORM.usado == False,
                QRAccesoORM.fecha_expiracion > ahora
            )
        ).order_by(desc(QRAccesoORM.fecha_generacion)).all()
        
        return [self._mapear_qr_a_dominio(orm) for orm in orms]
    
    def contar_registros_hoy(self) -> dict:
        """Cuenta los registros de acceso generados hoy"""
        hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        hoy_fin = hoy_inicio + timedelta(days=1)
        
        total = self.session.query(RegistroAccesoORM).filter(
            and_(
                RegistroAccesoORM.fecha_hora >= hoy_inicio,
                RegistroAccesoORM.fecha_hora < hoy_fin
            )
        ).count()
        
        ingresos = self.session.query(RegistroAccesoORM).filter(
            and_(
                RegistroAccesoORM.fecha_hora >= hoy_inicio,
                RegistroAccesoORM.fecha_hora < hoy_fin,
                RegistroAccesoORM.tipo_movimiento == "INGRESO"
            )
        ).count()
        
        salidas = self.session.query(RegistroAccesoORM).filter(
            and_(
                RegistroAccesoORM.fecha_hora >= hoy_inicio,
                RegistroAccesoORM.fecha_hora < hoy_fin,
                RegistroAccesoORM.tipo_movimiento == "SALIDA"
            )
        ).count()
        
        return {
            "total": total,
            "ingresos": ingresos,
            "salidas": salidas,
            "dentro_estimado": ingresos - salidas
        }

    def guardar_registro(self, registro: RegistroAcceso) -> None:
        """Guarda un nuevo registro de acceso"""
        orm = RegistroAccesoORM(
            usuario_id=registro.usuario.numero_documento.valor,
            tipo_movimiento=registro.tipo_movimiento,
            fecha_hora=registro.fecha_hora,
            vigilante_id=registro.vigilante_id,
            ubicacion=registro.ubicacion,
            pertenencias_declaradas=registro.pertenencias_declaradas,
            vehiculos_declarados=registro.vehiculos_declarados,
            observaciones=registro.observaciones,
            qr_usado_id=registro.qr_usado_id
        )
        
        self.session.add(orm)
        self.session.commit()
        registro.id = orm.id

    def limpiar_qrs_expirados(self) -> int:
        """Elimina QRs expirados y no usados"""
        ahora = datetime.now()
        eliminados = self.session.query(QRAccesoORM).filter(
            and_(
                QRAccesoORM.usado == False,
                QRAccesoORM.fecha_expiracion < ahora
            )
        ).delete()
        
        self.session.commit()
        return eliminados

    def listar_registros_por_fecha(self, fecha_inicio: datetime, fecha_fin: datetime, usuario_id: Optional[str] = None) -> List[RegistroAcceso]:
        """Lista registros de acceso dentro de un rango de fechas"""
        query = self.session.query(RegistroAccesoORM).filter(
            and_(
                RegistroAccesoORM.fecha_hora >= fecha_inicio,
                RegistroAccesoORM.fecha_hora <= fecha_fin
            )
        )
        
        if usuario_id:
            query = query.filter(RegistroAccesoORM.usuario_id == usuario_id)
        
        orms = query.order_by(desc(RegistroAccesoORM.fecha_hora)).all()
        return [self._mapear_registro_a_dominio(orm) for orm in orms]

    def marcar_qr_usado(self, qr_id: int, vigilante_id: str = None, ubicacion: str = None) -> None:
        """Marca un QR como usado"""
        qr_orm = self.session.query(QRAccesoORM).filter_by(id=qr_id).first()
        if qr_orm:
            qr_orm.usado = True
            qr_orm.fecha_uso = datetime.now()
            if vigilante_id:
                qr_orm.vigilante_uso = vigilante_id
            if ubicacion:
                qr_orm.ubicacion_uso = ubicacion
            self.session.commit()

    def obtener_ultimo_registro_usuario(self, usuario_id: str) -> Optional[RegistroAcceso]:
        """Obtiene el último registro de acceso de un usuario"""
        orm = (
            self.session.query(RegistroAccesoORM)
            .filter_by(usuario_id=usuario_id)
            .order_by(desc(RegistroAccesoORM.fecha_hora))
            .first()
        )

        if orm:
            return self._mapear_registro_a_dominio(orm)
        return None

    def obtener_usuarios_dentro(self) -> List[dict]:
        """Obtiene información de usuarios actualmente dentro del sistema"""
        # Subconsulta para obtener el último registro de cada usuario
        subquery = (
            self.session.query(
                RegistroAccesoORM.usuario_id,
                RegistroAccesoORM.tipo_movimiento,
                RegistroAccesoORM.fecha_hora
            )
            .distinct(RegistroAccesoORM.usuario_id)
            .order_by(
                RegistroAccesoORM.usuario_id,
                desc(RegistroAccesoORM.fecha_hora)
            )
            .subquery()
        )
        
        # Obtener usuarios cuyo último registro fue INGRESO
        usuarios_dentro = []
        for row in self.session.query(subquery).filter(
            subquery.c.tipo_movimiento == "INGRESO"
        ).all():
            
            usuario = self.repo_usuarios.obtener_por_id(row.usuario_id)
            if usuario:
                tiempo_dentro = datetime.now() - row.fecha_hora
                usuarios_dentro.append({
                    "usuario_id": row.usuario_id,
                    "nombre": f"{usuario.nombres.valor} {usuario.apellidos.valor}",
                    "rol": usuario.rol.value,
                    "fecha_ingreso": row.fecha_hora,
                    "tiempo_dentro_minutos": int(tiempo_dentro.total_seconds() / 60)
                })
        
        return usuarios_dentro