from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_
from app.modules.vehiculos.domain.puertos.repositorio_vehiculos import RepositorioVehiculos
from app.modules.vehiculos.domain.entidades.vehiculo import Vehiculo
from app.modules.vehiculos.infrastructure.modelos.modelo_vehiculo import VehiculoORM
from app.modules.autenticacion.domain.puertos.repositorio_usuarios import RepositorioUsuarios

class RepositorioVehiculosBD(RepositorioVehiculos):
    def __init__(self, session: Session, repo_usuarios: RepositorioUsuarios):
        self.session = session
        self.repo_usuarios = repo_usuarios

    def agregar(self, vehiculo: Vehiculo) -> None:
        # Validar que no existe la placa
        if self.existe_placa(vehiculo.placa.valor):
            raise ValueError(f"Ya existe un vehículo con la placa '{vehiculo.placa.valor}'")
        
        orm = VehiculoORM(
            placa          = vehiculo.placa.valor,
            tipo           = vehiculo.tipo.value,
            marca          = vehiculo.marca.valor,
            modelo         = vehiculo.modelo.valor,
            color          = vehiculo.color.valor,
            foto           = vehiculo.foto.valor,
            estado         = vehiculo.estado.value,
            usuario_id     = vehiculo.usuario.numero_documento.valor,
            fecha_registro = vehiculo.fecha_registro
        )
        self.session.add(orm)
        self.session.commit()

    def obtener_por_placa(self, placa: str) -> Optional[Vehiculo]:
        """Obtiene un vehículo por su placa (primary key)."""
        orm = self.session.query(VehiculoORM).filter_by(placa=placa.upper()).first()
        if not orm:
            return None
        return self._mapear_a_dominio(orm)

    def listar_por_usuario(self, usuario_id: str, incluir_inactivos: bool = False) -> List[Vehiculo]:
        query = self.session.query(VehiculoORM).filter_by(usuario_id=usuario_id)
        
        if not incluir_inactivos:
            query = query.filter_by(estado="Activo")
        
        # Ordenar por fecha de registro descendente
        orms = query.order_by(desc(VehiculoORM.fecha_registro)).all()
        return [self._mapear_a_dominio(orm) for orm in orms]

    def listar_por_tipo(self, tipo: str, incluir_inactivos: bool = False) -> List[Vehiculo]:
        """Lista vehículos por tipo."""
        query = self.session.query(VehiculoORM).filter_by(tipo=tipo)
        
        if not incluir_inactivos:
            query = query.filter_by(estado="Activo")
        
        orms = query.order_by(desc(VehiculoORM.fecha_registro)).all()
        return [self._mapear_a_dominio(orm) for orm in orms]

    def buscar_por_marca_modelo(self, termino: str, usuario_id: Optional[str] = None, incluir_inactivos: bool = False) -> List[Vehiculo]:
        """Busca vehículos por marca o modelo (búsqueda parcial)."""
        query = self.session.query(VehiculoORM).filter(
            or_(
                VehiculoORM.marca.ilike(f"%{termino}%"),
                VehiculoORM.modelo.ilike(f"%{termino}%")
            )
        )
        
        if usuario_id:
            query = query.filter_by(usuario_id=usuario_id)
        
        if not incluir_inactivos:
            query = query.filter_by(estado="Activo")
        
        orms = query.order_by(asc(VehiculoORM.marca), asc(VehiculoORM.modelo)).all()
        return [self._mapear_a_dominio(orm) for orm in orms]

    def contar_por_usuario(self, usuario_id: str) -> dict:
        """Retorna estadísticas de vehículos por usuario."""
        total = self.session.query(VehiculoORM).filter_by(usuario_id=usuario_id).count()
        activos = self.session.query(VehiculoORM).filter_by(
            usuario_id=usuario_id, estado="Activo"
        ).count()
        inactivos = total - activos
        
        # Contar por tipos (solo activos para el reporte por tipo)
        from sqlalchemy import func
        tipos_result = self.session.query(
            VehiculoORM.tipo,
            func.count(VehiculoORM.tipo).label('cantidad')
        ).filter_by(
            usuario_id=usuario_id, 
            estado="Activo"
        ).group_by(VehiculoORM.tipo).all()
        
        # Convertir resultado a diccionario
        por_tipo = {tipo: cantidad for tipo, cantidad in tipos_result}
        
        return {
            "total": total,
            "activos": activos,
            "inactivos": inactivos,
            "por_tipo": por_tipo
        }

    def actualizar(self, vehiculo: Vehiculo) -> None:
        orm = self.session.query(VehiculoORM).filter_by(placa=vehiculo.placa.valor).first()
        if not orm:
            raise ValueError("Vehículo no encontrado para actualizar")
        
        orm.tipo           = vehiculo.tipo.value
        orm.marca          = vehiculo.marca.valor
        orm.modelo         = vehiculo.modelo.valor
        orm.color          = vehiculo.color.valor
        orm.foto           = vehiculo.foto.valor
        orm.estado         = vehiculo.estado.value
        orm.usuario_id     = vehiculo.usuario.numero_documento.valor
        
        self.session.commit()

    def eliminar(self, placa: str) -> None:
        """Elimina un vehículo por su placa."""
        orm = self.session.query(VehiculoORM).filter_by(placa=placa.upper()).first()
        if orm:
            self.session.delete(orm)
            self.session.commit()
        else:
            raise ValueError("Vehículo no encontrado para eliminar")

    def existe_placa(self, placa: str) -> bool:
        """Verifica si existe un vehículo con la placa dada."""
        return self.session.query(VehiculoORM).filter_by(placa=placa.upper()).first() is not None

    def _mapear_a_dominio(self, orm: VehiculoORM) -> Vehiculo:
        from app.modules.vehiculos.domain.objetos_de_valor.placa_vehiculo import PlacaVehiculo
        from app.modules.vehiculos.domain.objetos_de_valor.tipo_vehiculo import TipoVehiculo
        from app.modules.vehiculos.domain.objetos_de_valor.marca_vehiculo import MarcaVehiculo
        from app.modules.vehiculos.domain.objetos_de_valor.modelo_vehiculo import ModeloVehiculo
        from app.modules.vehiculos.domain.objetos_de_valor.color_vehiculo import ColorVehiculo
        from app.modules.vehiculos.domain.objetos_de_valor.foto_vehiculo import FotoVehiculo
        from app.modules.vehiculos.domain.objetos_de_valor.estado_vehiculo import EstadoVehiculo

        # Buscar el usuario real usando el repositorio de usuarios
        usuario = self.repo_usuarios.obtener_por_id(orm.usuario_id)
        if not usuario:
            raise ValueError("Usuario propietario no encontrado")

        # Crear placa con validación de tipo
        tipo_vehiculo = TipoVehiculo(orm.tipo)
        placa_vehiculo = PlacaVehiculo.crear_para_tipo(orm.placa, tipo_vehiculo)

        return Vehiculo(
            placa=placa_vehiculo,
            tipo=tipo_vehiculo,
            marca=MarcaVehiculo(orm.marca),
            modelo=ModeloVehiculo(orm.modelo),
            color=ColorVehiculo(orm.color),
            foto=FotoVehiculo(orm.foto or ""),
            estado=EstadoVehiculo(orm.estado),
            usuario=usuario,
            fecha_registro=orm.fecha_registro
        )