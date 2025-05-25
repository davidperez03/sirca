'''
repositorio de usuarios
Este repositorio se encarga de la persistencia de los usuarios en la base de datos.
va de la mano con el puerto de repositorio de usuarios definido en el dominio.
El repositorio utiliza SQLAlchemy para interactuar con la base de datos y realizar operaciones CRUD (Crear, Leer, Actualizar, Eliminar) sobre los usuarios.
'''

# Biblioteca estándar
from typing import Optional

# ORM de terceros
from sqlalchemy.orm import Session

# Puertos del dominio
from app.modules.autenticacion.domain.puertos.repositorio_usuarios import RepositorioUsuarios

# Entidades del dominio
from app.modules.autenticacion.domain.entidades.usuario import Usuario as UsuarioDominio

# Objetos de valor del dominio
from app.modules.autenticacion.domain.objetos_de_valor.enums.tipo_documento import TipoDocumento
from app.modules.autenticacion.domain.objetos_de_valor.enums.rol_usuario import RolUsuario
from app.modules.autenticacion.domain.objetos_de_valor.numero_documento import NumeroDocumento
from app.modules.autenticacion.domain.objetos_de_valor.nombre_propio import NombrePropio
from app.modules.autenticacion.domain.objetos_de_valor.correo_institucional import CorreoInstitucional
from app.modules.autenticacion.domain.objetos_de_valor.contrasena import Contrasena

# Modelos de infraestructura
from app.modules.autenticacion.infrastructure.modelos.modelo_usuario import UsuarioORM

class RepositorioUsuariosBD(RepositorioUsuarios):
    def __init__(self, session: Session):
        self.session = session

    def guardar(self, usuario: UsuarioDominio) -> None:
        db_usuario = UsuarioORM(
            numero_documento     = usuario.numero_documento.valor,
            tipo_documento       = usuario.tipo_documento.name,
            nombres              = usuario.nombres.valor,
            apellidos            = usuario.apellidos.valor,
            correo_institucional = usuario.correo_institucional.valor,
            contrasena           = usuario.contrasena.hash,
            activo               = usuario.activo,
            rol                  = usuario.rol.value
        )
        self.session.add(db_usuario)
        self.session.commit()

    def obtener_por_id(self, numero_documento: str) -> Optional[UsuarioDominio]:
        orm = (
            self.session
                .query(UsuarioORM)
                .filter_by(numero_documento=numero_documento)
                .first()
        )
        if not orm:
            return None

        tipo_doc      = TipoDocumento[orm.tipo_documento]
        numero_vo     = NumeroDocumento(tipo_doc, orm.numero_documento)
        nombres_vo    = NombrePropio(orm.nombres)
        apellidos_vo  = NombrePropio(orm.apellidos)
        correo_vo     = CorreoInstitucional(orm.correo_institucional)
        contrasena_vo = Contrasena(orm.contrasena)
        rol_vo        = RolUsuario(orm.rol)

        return UsuarioDominio(
            tipo_documento       = tipo_doc,
            numero_documento     = numero_vo,
            nombres              = nombres_vo,
            apellidos            = apellidos_vo,
            correo_institucional = correo_vo,
            contrasena           = contrasena_vo,
            activo               = orm.activo,
            rol                  = rol_vo       
        )

    def obtener_por_correo(self, correo: str) -> Optional[UsuarioDominio]:
        orm = (
            self.session
            .query(UsuarioORM)
            .filter(UsuarioORM.correo_institucional == correo)
            .first()
        )
        if not orm:
            return None

        tipo_doc      = TipoDocumento[orm.tipo_documento]
        numero_vo     = NumeroDocumento(tipo_doc, orm.numero_documento)
        nombres_vo    = NombrePropio(orm.nombres)
        apellidos_vo  = NombrePropio(orm.apellidos)
        correo_vo     = CorreoInstitucional(orm.correo_institucional)
        contrasena_vo = Contrasena(orm.contrasena)
        rol_vo        = RolUsuario(orm.rol)

        return UsuarioDominio(
            tipo_documento       = tipo_doc,
            numero_documento     = numero_vo,
            nombres              = nombres_vo,
            apellidos            = apellidos_vo,
            correo_institucional = correo_vo,
            contrasena           = contrasena_vo,
            activo               = orm.activo,
            rol                  = rol_vo
        )

    def actualizar(self, usuario: UsuarioDominio) -> None:
        orm = (
            self.session
            .query(UsuarioORM)
            .filter_by(numero_documento=usuario.numero_documento.valor)
            .first()
        )
        if not orm:
            raise ValueError("Usuario no existe para actualizar")

        orm.nombres              = usuario.nombres.valor
        orm.apellidos            = usuario.apellidos.valor
        orm.correo_institucional = usuario.correo_institucional.valor
        orm.contrasena           = usuario.contrasena.hash
        orm.activo               = usuario.activo
        orm.rol                  = usuario.rol.value

        self.session.commit()

    def obtener_por_rol(self, rol: RolUsuario) -> list[UsuarioDominio]:
        usuarios_orm = (
            self.session
            .query(UsuarioORM)
            .filter(UsuarioORM.rol == rol.value)
            .all()
        )

        usuarios = []
        for orm in usuarios_orm:
            tipo_doc      = TipoDocumento[orm.tipo_documento]
            numero_vo     = NumeroDocumento(tipo_doc, orm.numero_documento)
            nombres_vo    = NombrePropio(orm.nombres)
            apellidos_vo  = NombrePropio(orm.apellidos)
            correo_vo     = CorreoInstitucional(orm.correo_institucional)
            contrasena_vo = Contrasena(orm.contrasena)
            rol_vo        = RolUsuario(orm.rol)

            usuarios.append(UsuarioDominio(
                tipo_documento       = tipo_doc,
                numero_documento     = numero_vo,
                nombres              = nombres_vo,
                apellidos            = apellidos_vo,
                correo_institucional = correo_vo,
                contrasena           = contrasena_vo,
                activo               = orm.activo,
                rol                  = rol_vo
            ))

        return usuarios