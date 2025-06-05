from app.modules.pertenencias.domain.puertos.repositorio_pertenencias import RepositorioPertenencias
from app.modules.pertenencias.infrastructure.servicios.servicio_archivos import ServicioArchivos

class EliminarPertenencia:
    def __init__(self, repositorio: RepositorioPertenencias):
        self.repositorio = repositorio
        self.servicio_archivos = ServicioArchivos()

    def ejecutar(self, id_pertenencia: int, usuario_id: str) -> None:
        """
        Elimina una pertenencia y su archivo de imagen asociado.
        Incluye validación de propiedad.
        """
        # 1. Obtener la pertenencia
        pertenencia = self.repositorio.obtener_por_id(id_pertenencia)
        if not pertenencia:
            raise ValueError("Pertenencia no encontrada")
        
        # 2. Verificar que pertenece al usuario
        if pertenencia.usuario.numero_documento.valor != usuario_id:
            raise ValueError("No tienes permisos para eliminar esta pertenencia")
        
        # 3. Eliminar archivo de imagen si existe
        if pertenencia.foto.valor:
            self.servicio_archivos.eliminar_imagen(pertenencia.foto.valor)
        
        # 4. Eliminar de la base de datos
        self.repositorio.eliminar(id_pertenencia)

    def ejecutar_admin(self, id_pertenencia: int) -> None:
        """
        Versión para administradores que pueden eliminar cualquier pertenencia.
        """
        # 1. Obtener la pertenencia
        pertenencia = self.repositorio.obtener_por_id(id_pertenencia)
        if not pertenencia:
            raise ValueError("Pertenencia no encontrada")
        
        # 2. Eliminar archivo de imagen si existe
        if pertenencia.foto.valor:
            self.servicio_archivos.eliminar_imagen(pertenencia.foto.valor)
        
        # 3. Eliminar de la base de datos
        self.repositorio.eliminar(id_pertenencia)