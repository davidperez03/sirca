'''
    Repositorio de Usuarios
    Interfaz que define las operaciones para interactuar con la persistencia de datos de los usuarios.
    Permite guardar, obtener y actualizar usuarios en la base de datos.
    Se utiliza para separar la lógica de negocio de la lógica de acceso a datos, facilitando el mantenimiento y la escalabilidad del sistema.
'''
# Biblioteca estándar
from abc import ABC, abstractmethod

# Biblioteca estándar — tipado
from typing import Optional

# Entidades del dominio
from app.modules.autenticacion.domain.entidades.usuario import Usuario

class RepositorioUsuarios(ABC):
    @abstractmethod
    def guardar(self, usuario: Usuario) -> None:
        """Persiste un Usuario nuevo."""
        raise NotImplementedError

    @abstractmethod
    def obtener_por_id(self, numero_documento: str) -> Optional[Usuario]:
        """Recupera un Usuario por su número de documento."""
        raise NotImplementedError

    @abstractmethod
    def obtener_por_correo(self, correo: str) -> Optional[Usuario]:
        """Recupera un Usuario por su correo institucional."""
        raise NotImplementedError

    @abstractmethod
    def actualizar(self, usuario: Usuario) -> None:
        """Actualiza datos de un Usuario ya existente (p.ej. su token o estado)."""
        raise NotImplementedError
    