from typing import Optional
from fastapi import UploadFile
from app.modules.vehiculos.domain.entidades.vehiculo import Vehiculo
from app.modules.vehiculos.domain.objetos_de_valor.tipo_vehiculo import TipoVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.marca_vehiculo import MarcaVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.modelo_vehiculo import ModeloVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.color_vehiculo import ColorVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.foto_vehiculo import FotoVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.estado_vehiculo import EstadoVehiculo
from app.modules.vehiculos.domain.puertos.repositorio_vehiculos import RepositorioVehiculos
from app.modules.vehiculos.infrastructure.servicios.servicio_archivos_vehiculos import ServicioArchivosVehiculos

class ActualizarVehiculo:
    def __init__(self, repositorio: RepositorioVehiculos):
        self.repositorio = repositorio
        self.servicio_archivos = ServicioArchivosVehiculos()

    async def ejecutar(
        self,
        placa: str,
        tipo: Optional[str] = None,
        marca: Optional[str] = None,
        modelo: Optional[str] = None,
        color: Optional[str] = None,
        estado: Optional[str] = None,
        archivo_foto: Optional[UploadFile] = None,
        eliminar_foto: bool = False
    ) -> Vehiculo:
        
        # 1. Obtener vehículo existente
        vehiculo = self.repositorio.obtener_por_placa(placa)
        if not vehiculo:
            raise ValueError("Vehículo no encontrado")
        
        # 2. Actualizar campos si se proporcionan
        if tipo is not None:
            vehiculo.tipo = TipoVehiculo(tipo)
        
        if marca is not None:
            vehiculo.marca = MarcaVehiculo(marca)
        
        if modelo is not None:
            vehiculo.modelo = ModeloVehiculo(modelo)
        
        if color is not None:
            vehiculo.color = ColorVehiculo(color)
        
        if estado is not None:
            vehiculo.estado = EstadoVehiculo(estado)
        
        # 3. Manejar foto
        if eliminar_foto:
            # Eliminar foto actual
            if vehiculo.foto.valor:
                self.servicio_archivos.eliminar_imagen(vehiculo.foto.valor)
            vehiculo.foto = FotoVehiculo("")
        
        elif archivo_foto:
            # Eliminar foto anterior si existe
            if vehiculo.foto.valor:
                self.servicio_archivos.eliminar_imagen(vehiculo.foto.valor)
            
            # Guardar nueva foto
            try:
                nueva_ruta = await self.servicio_archivos.guardar_imagen_vehiculo(
                    archivo_foto,
                    vehiculo.usuario.numero_documento.valor
                )
                vehiculo.foto = FotoVehiculo(nueva_ruta)
            except Exception as e:
                raise ValueError(f"Error al procesar la imagen: {str(e)}")
        
        # 4. Actualizar en repositorio
        self.repositorio.actualizar(vehiculo)
        
        return vehiculo

    def ejecutar_sin_archivo(
        self,
        placa: str,
        tipo: Optional[str] = None,
        marca: Optional[str] = None,
        modelo: Optional[str] = None,
        color: Optional[str] = None,
        estado: Optional[str] = None,
        foto_ruta: Optional[str] = None,
        eliminar_foto: bool = False
    ) -> Vehiculo:
        """Versión síncrona para cuando no se maneja archivo de subida."""
        
        # 1. Obtener vehículo existente
        vehiculo = self.repositorio.obtener_por_placa(placa)
        if not vehiculo:
            raise ValueError("Vehículo no encontrado")
        
        # 2. Actualizar campos básicos
        if tipo is not None:
            vehiculo.tipo = TipoVehiculo(tipo)
        
        if marca is not None:
            vehiculo.marca = MarcaVehiculo(marca)
        
        if modelo is not None:
            vehiculo.modelo = ModeloVehiculo(modelo)
        
        if color is not None:
            vehiculo.color = ColorVehiculo(color)
        
        if estado is not None:
            vehiculo.estado = EstadoVehiculo(estado)
        
        # 3. Manejar foto
        if eliminar_foto:
            if vehiculo.foto.valor:
                self.servicio_archivos.eliminar_imagen(vehiculo.foto.valor)
            vehiculo.foto = FotoVehiculo("")
        elif foto_ruta is not None:
            vehiculo.foto = FotoVehiculo(foto_ruta)
        
        # 4. Actualizar
        self.repositorio.actualizar(vehiculo)
        
        return vehiculo