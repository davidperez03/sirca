from app.modules.vehiculos.domain.puertos.repositorio_vehiculos import RepositorioVehiculos
from app.modules.vehiculos.infrastructure.servicios.servicio_archivos_vehiculos import ServicioArchivosVehiculos

class EliminarVehiculo:
    def __init__(self, repositorio: RepositorioVehiculos):
        self.repositorio = repositorio
        self.servicio_archivos = ServicioArchivosVehiculos()

    def ejecutar(self, placa: str, usuario_id: str) -> None:
        """
        Elimina un vehículo y su archivo de imagen asociado.
        Incluye validación de propiedad.
        """
        # 1. Obtener el vehículo
        vehiculo = self.repositorio.obtener_por_placa(placa)
        if not vehiculo:
            raise ValueError("Vehículo no encontrado")
        
        # 2. Verificar que pertenece al usuario
        if vehiculo.usuario.numero_documento.valor != usuario_id:
            raise ValueError("No tienes permisos para eliminar este vehículo")
        
        # 3. Eliminar archivo de imagen si existe
        if vehiculo.foto.valor:
            self.servicio_archivos.eliminar_imagen(vehiculo.foto.valor)
        
        # 4. Eliminar de la base de datos
        self.repositorio.eliminar(placa)

    def ejecutar_admin(self, placa: str) -> None:
        """Versión para administradores que pueden eliminar cualquier vehículo."""
        
        # 1. Obtener el vehículo
        vehiculo = self.repositorio.obtener_por_placa(placa)
        if not vehiculo:
            raise ValueError("Vehículo no encontrado")
        
        # 2. Eliminar archivo de imagen si existe
        if vehiculo.foto.valor:
            self.servicio_archivos.eliminar_imagen(vehiculo.foto.valor)
        
        # 3. Eliminar de la base de datos
        self.repositorio.eliminar(placa)