'''
    modelo ORM para la tabla de usuarios.
    Este modelo define la estructura de la tabla de usuarios en la base de datos.
    Utiliza SQLAlchemy para definir los campos y sus tipos de datos.
'''

# Librerías de terceros
from sqlalchemy import Column, String, Boolean

# Dependencia interna para el modelo
from app.core.dependencias import Base

class UsuarioORM(Base):
    __tablename__ = "usuarios"

    numero_documento        = Column(String, primary_key=True, index=True)
    tipo_documento          = Column(String, nullable=False)
    nombres                 = Column(String, nullable=False)
    apellidos               = Column(String, nullable=False)
    correo_institucional    = Column(String, nullable=False, unique=True)
    contrasena              = Column("contrasena", String, nullable=False)
    activo                  = Column(Boolean, default=False)
    rol                     = Column(String, nullable=False)