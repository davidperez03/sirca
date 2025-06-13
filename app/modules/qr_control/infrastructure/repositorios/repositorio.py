from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_
from datetime import datetime, timedelta
from app.modules.qr_control.domain.puertos.repositorio_accesos import RepositorioAccesos
from app.modules.qr_control.domain.entidades.registro_acceso import RegistroAcceso
from app.modules.qr_control.domain.entidades.qr_temporal import QRTemporal
from app.modules.qr_control.infrastructure.modelos.modelo_registro_acceso import RegistroAccesoORM
from app.modules.qr_control.infrastructure.modelos.modelo_qr_temporal import QRTemporalORM
from app.modules.autenticacion.domain.puertos.repositorio_usuarios import RepositorioUsuarios

class RepositorioAccesosBD(RepositorioAccesos):
    def __init__(self, session: Session, repo_usuarios: RepositorioUsuarios):
        self.session = session
        self.repo_usuarios = repo_usuarios

    def guardar_registro(self, registro: RegistroAcceso) -> None:
        orm = RegistroAccesoORM(
            usuario_id=registro.usuario.numero_documento.valor,
            tipo_movimiento=registro.tipo_movimiento,
            fecha_hora=registro.fecha_hora,
            vigilante_id=registro.vigilante_id,
            ubicacion=registro.ubicacion,
            items_declarados=registro.items_declarados,
            observaciones=registro.observaciones
        )
        self.session.add(orm)
        self.session.commit()
        registro.id = orm.id

    def obtener_ultimo_acceso(self, usuario_id: str) -> Optional[RegistroAcceso]:
        orm = (self.session.query(RegistroAccesoORM)
               .filter_by(usuario_id=usuario_id)
               .order_by(desc(RegistroAccesoORM.fecha_hora))
               .first())
        
        if not orm:
            return None
        return self._mapear_a_dominio(orm)

    def listar_accesos_por_fecha(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[RegistroAcceso]:
        orms = (self.session.query(RegistroAccesoORM)
                .filter(and_(
                    RegistroAccesoORM.fecha_hora >= fecha_inicio,
                    RegistroAccesoORM.fecha_hora <= fecha_fin
                ))
                .order_by(desc(RegistroAccesoORM.fecha_hora))
                .all())
        
        return [self._mapear_a_dominio(orm) for orm in orms]

    def guardar_qr_temporal(self, qr: QRTemporal) -> None:
        # Limpiar QRs anteriores del usuario que no han sido usados
        self.session.query(QRTemporalORM).filter(
            and_(
                QRTemporalORM.usuario_id == qr.usuario_id,
                QRTemporalORM.usado == False
            )
        ).delete()
        
        orm = QRTemporalORM(
            usuario_id=qr.usuario_id,
            codigo_qr=qr.codigo_qr,
            fecha_generacion=qr.fecha_generacion,
            fecha_expiracion=qr.fecha_expiracion,
            usado=qr.usado
        )
        self.session.add(orm)
        self.session.commit()
        qr.id = orm.id

    def obtener_qr_temporal(self, codigo: str) -> Optional[QRTemporal]:
        orm = (self.session.query(QRTemporalORM)
               .filter_by(codigo_qr=codigo)
               .first())
        
        if not orm:
            return None
        return self._mapear_qr_a_dominio(orm)

    def marcar_qr_usado(self, codigo: str, vigilante_id: str) -> None:
        self.session.query(QRTemporalORM).filter_by(codigo_qr=codigo).update({
            'usado': True,
            'fecha_uso': datetime.now(),
            'vigilante_uso': vigilante_id
        })
        self.session.commit()

    def limpiar_qr_expirados(self) -> int:
        count = self.session.query(QRTemporalORM).filter(
            QRTemporalORM.fecha_expiracion < datetime.now()
        ).delete()
        self.session.commit()
        return count

    def obtener_estado_usuario(self, usuario_id: str) -> str:
        ultimo_acceso = self.obtener_ultimo_acceso(usuario_id)
        if not ultimo_acceso:
            return "FUERA"  # Primera vez
        
        return "DENTRO" if ultimo_acceso.tipo_movimiento == "INGRESO" else "FUERA"

    def _mapear_a_dominio(self, orm: RegistroAccesoORM) -> RegistroAcceso:
        usuario = self.repo_usuarios.obtener_por_id(orm.usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        return RegistroAcceso(
            usuario=usuario,
            tipo_movimiento=orm.tipo_movimiento,
            fecha_hora=orm.fecha_hora,
            vigilante_id=orm.vigilante_id,
            ubicacion=orm.ubicacion,
            items_declarados=orm.items_declarados or [],
            observaciones=orm.observaciones or "",
            id=orm.id
        )

    def _mapear_qr_a_dominio(self, orm: QRTemporalORM) -> QRTemporal:
        return QRTemporal(
            usuario_id=orm.usuario_id,
            codigo_qr=orm.codigo_qr,
            fecha_generacion=orm.fecha_generacion,
            fecha_expiracion=orm.fecha_expiracion,
            usado=orm.usado,
            fecha_uso=orm.fecha_uso,
            vigilante_uso=orm.vigilante_uso,
            id=orm.id
        )