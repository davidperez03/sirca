from typing import List, Optional
from sqlalchemy.orm import Session
from app.modules.pertenencias.domain.puertos.repositorio_pertenencias import RepositorioPertenencias
from app.modules.pertenencias.domain.entidades.pertenencia import Pertenencia
from app.modules.pertenencias.infrastructure.modelos.modelo_pertenencia import PertenenciaORM
from app.modules.autenticacion.domain.puertos.repositorio_usuarios import RepositorioUsuarios
from app.modules.autenticacion.infrastructure.repositorios.repositorio import RepositorioUsuariosBD

class RepositorioPertenenciasBD(RepositorioPertenencias):
    def __init__(self, session: Session, repo_usuarios: RepositorioUsuarios):
        self.session = session
        self.repo_usuarios = repo_usuarios

    def agregar(self, pertenencia: Pertenencia) -> None:
        orm = PertenenciaORM(
            serial         = pertenencia.serial.valor,
            nombre         = pertenencia.nombre.valor,
            tipo           = pertenencia.tipo.value,
            descripcion    = pertenencia.descripcion.valor,
            foto           = pertenencia.foto.valor,
            estado         = pertenencia.estado.value,
            usuario_id     = pertenencia.usuario.numero_documento.valor,
            fecha_registro = pertenencia.fecha_registro
        )
        self.session.add(orm)
        self.session.commit()

    def obtener_por_serial(self, serial: str) -> Optional[Pertenencia]:
        orm = self.session.query(PertenenciaORM).filter_by(serial=serial).first()
        if not orm:
            return None
        return self._mapear_a_dominio(orm)

    def listar_por_usuario(self, usuario_id: str) -> List[Pertenencia]:
        orms = self.session.query(PertenenciaORM).filter_by(usuario_id=usuario_id).all()
        return [self._mapear_a_dominio(orm) for orm in orms]

    def actualizar(self, pertenencia: Pertenencia) -> None:
        orm = self.session.query(PertenenciaORM).filter_by(serial=pertenencia.serial.valor).first()
        if not orm:
            raise ValueError("Pertenencia no encontrada para actualizar")
        orm.nombre         = pertenencia.nombre.valor
        orm.tipo           = pertenencia.tipo.value
        orm.descripcion    = pertenencia.descripcion.valor
        orm.foto           = pertenencia.foto.valor
        orm.estado         = pertenencia.estado.value
        orm.usuario_id     = pertenencia.usuario.numero_documento.valor
        orm.fecha_registro = pertenencia.fecha_registro
        self.session.commit()

    def eliminar(self, serial: str) -> None:
        orm = self.session.query(PertenenciaORM).filter_by(serial=serial).first()
        if orm:
            self.session.delete(orm)
            self.session.commit()

    def _mapear_a_dominio(self, orm: PertenenciaORM) -> Pertenencia:
        from app.modules.pertenencias.domain.objetos_de_valor.nombre_pertenencia import NombrePertenencia
        from app.modules.pertenencias.domain.objetos_de_valor.tipo_pertenencia import TipoPertenencia
        from app.modules.pertenencias.domain.objetos_de_valor.descripcion_pertenencia import DescripcionPertenencia
        from app.modules.pertenencias.domain.objetos_de_valor.serial_pertenencia import SerialPertenencia
        from app.modules.pertenencias.domain.objetos_de_valor.foto_pertenencia import FotoPertenencia
        from app.modules.pertenencias.domain.objetos_de_valor.estado_pertenencia import EstadoPertenencia

        # Buscar el usuario real usando el repositorio de usuarios
        usuario = self.repo_usuarios.obtener_por_id(orm.usuario_id)
        if not usuario:
            raise ValueError("Usuario propietario no encontrado")

        return Pertenencia(
            nombre=NombrePertenencia(orm.nombre),
            tipo=TipoPertenencia(orm.tipo),
            descripcion=DescripcionPertenencia(orm.descripcion),
            serial=SerialPertenencia(orm.serial),
            foto=FotoPertenencia(orm.foto),
            estado=EstadoPertenencia(orm.estado),
            usuario=usuario,
            fecha_registro=orm.fecha_registro
        )

# Ejemplo de inicialización
session = ...  # tu sesión de SQLAlchemy
repo_usuarios = RepositorioUsuariosBD(session)
repo_pertenencias = RepositorioPertenenciasBD(session, repo_usuarios)