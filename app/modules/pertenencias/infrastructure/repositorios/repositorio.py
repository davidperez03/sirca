from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
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
        # Validar que no existe el serial si tiene valor y no está vacío
        if pertenencia.serial.valor and pertenencia.serial.valor.strip():
            existente = self.session.query(PertenenciaORM).filter_by(serial=pertenencia.serial.valor).first()
            if existente:
                raise ValueError(f"Ya existe una pertenencia con el serial '{pertenencia.serial.valor}'")
        
        orm = PertenenciaORM(
            serial         = pertenencia.serial.valor if pertenencia.serial.valor else None,
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
        
        # Actualizar el ID en la entidad
        pertenencia.id = orm.id

    def obtener_por_id(self, id: int) -> Optional[Pertenencia]:
        """Obtiene una pertenencia por su ID único."""
        orm = self.session.query(PertenenciaORM).filter_by(id=id).first()
        if not orm:
            return None
        return self._mapear_a_dominio(orm)

    def obtener_por_serial(self, serial: str) -> Optional[Pertenencia]:
        """Obtiene una pertenencia por su serial (si tiene)."""
        if not serial or not serial.strip():
            return None
        orm = self.session.query(PertenenciaORM).filter_by(serial=serial).first()
        if not orm:
            return None
        return self._mapear_a_dominio(orm)

    def listar_por_usuario(self, usuario_id: str, incluir_inactivos: bool = False) -> List[Pertenencia]:
        query = self.session.query(PertenenciaORM).filter_by(usuario_id=usuario_id)
        
        if not incluir_inactivos:
            query = query.filter_by(estado="Activo")
        
        # Ordenar por fecha de registro descendente
        orms = query.order_by(desc(PertenenciaORM.fecha_registro)).all()
        return [self._mapear_a_dominio(orm) for orm in orms]

    def listar_por_tipo(self, tipo: str, incluir_inactivos: bool = False) -> List[Pertenencia]:
        """Lista pertenencias por tipo."""
        query = self.session.query(PertenenciaORM).filter_by(tipo=tipo)
        
        if not incluir_inactivos:
            query = query.filter_by(estado="Activo")
        
        orms = query.order_by(desc(PertenenciaORM.fecha_registro)).all()
        return [self._mapear_a_dominio(orm) for orm in orms]

    def buscar_por_nombre(self, termino: str, usuario_id: Optional[str] = None, incluir_inactivos: bool = False) -> List[Pertenencia]:
        """Busca pertenencias por nombre (búsqueda parcial)."""
        query = self.session.query(PertenenciaORM).filter(
            PertenenciaORM.nombre.ilike(f"%{termino}%")
        )
        
        if usuario_id:
            query = query.filter_by(usuario_id=usuario_id)
        
        if not incluir_inactivos:
            query = query.filter_by(estado="Activo")
        
        orms = query.order_by(asc(PertenenciaORM.nombre)).all()
        return [self._mapear_a_dominio(orm) for orm in orms]

    def contar_por_usuario(self, usuario_id: str) -> dict:
        """Retorna estadísticas de pertenencias por usuario."""
        total = self.session.query(PertenenciaORM).filter_by(usuario_id=usuario_id).count()
        activas = self.session.query(PertenenciaORM).filter_by(
            usuario_id=usuario_id, estado="Activo"
        ).count()
        inactivas = total - activas
        
        # Contar por tipos (solo activas para el reporte por tipo)
        from sqlalchemy import func
        tipos_result = self.session.query(
            PertenenciaORM.tipo,
            func.count(PertenenciaORM.tipo).label('cantidad')
        ).filter_by(
            usuario_id=usuario_id, 
            estado="Activo"
        ).group_by(PertenenciaORM.tipo).all()
        
        # Convertir resultado a diccionario
        por_tipo = {tipo: cantidad for tipo, cantidad in tipos_result}
        
        return {
            "total": total,
            "activas": activas,
            "inactivas": inactivas,
            "por_tipo": por_tipo
        }

    def actualizar(self, pertenencia: Pertenencia) -> None:
        orm = self.session.query(PertenenciaORM).filter_by(id=pertenencia.id).first()
        if not orm:
            raise ValueError("Pertenencia no encontrada para actualizar")
        
        # Verificar unicidad del serial si cambió y no está vacío
        if (pertenencia.serial.valor and 
            pertenencia.serial.valor.strip() and 
            orm.serial != pertenencia.serial.valor):
            existente = self.session.query(PertenenciaORM).filter_by(serial=pertenencia.serial.valor).first()
            if existente:
                raise ValueError(f"Ya existe una pertenencia con el serial '{pertenencia.serial.valor}'")
        
        orm.nombre         = pertenencia.nombre.valor
        orm.tipo           = pertenencia.tipo.value
        orm.descripcion    = pertenencia.descripcion.valor
        orm.foto           = pertenencia.foto.valor
        orm.estado         = pertenencia.estado.value
        orm.usuario_id     = pertenencia.usuario.numero_documento.valor
        orm.serial         = pertenencia.serial.valor if pertenencia.serial.valor else None
        
        self.session.commit()

    def eliminar(self, id: int) -> None:
        """Elimina una pertenencia por su ID."""
        orm = self.session.query(PertenenciaORM).filter_by(id=id).first()
        if orm:
            self.session.delete(orm)
            self.session.commit()
        else:
            raise ValueError("Pertenencia no encontrada para eliminar")

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

        # Crear serial con la información del tipo para validación
        tipo_pertenencia = TipoPertenencia(orm.tipo)
        serial_pertenencia = SerialPertenencia.crear_para_tipo(orm.serial, tipo_pertenencia)

        return Pertenencia(
            nombre=NombrePertenencia(orm.nombre),
            tipo=tipo_pertenencia,
            descripcion=DescripcionPertenencia(orm.descripcion or ""),
            serial=serial_pertenencia,
            foto=FotoPertenencia(orm.foto or ""),
            estado=EstadoPertenencia(orm.estado),
            usuario=usuario,
            fecha_registro=orm.fecha_registro,
            id=orm.id  # Incluir el ID
        )