from datetime import datetime
from typing import Optional
from fastapi import UploadFile
from app.core.utils.fechas import obtener_fecha_local
from app.modules.vehiculos.domain.entidades.vehiculo import Vehiculo
from app.modules.vehiculos.domain.objetos_de_valor.placa_vehiculo import PlacaVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.tipo_vehiculo import TipoVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.marca_vehiculo import MarcaVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.modelo_vehiculo import ModeloVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.color_vehiculo import ColorVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.foto_vehiculo import FotoVehiculo
from app.modules.vehiculos.domain.objetos_de_valor.estado_vehiculo import EstadoVehiculo
from app.modules.vehiculos.domain.puertos.repositorio_vehiculos import RepositorioVehiculos
from app.modules.vehiculos.infrastructure.servicios.servicio_archivos_vehiculos import ServicioArchivosVehiculos
from app.modules.autenticacion.domain.entidades.usuario import Usuario

class RegistrarVehiculo:
    def __init__(self, repositorio: RepositorioVehiculos):
        self.repositorio = repositorio
        self.servicio_archivos = ServicioArchivosVehiculos()

    def _es_archivo_valido(self, archivo: Optional[UploadFile]) -> bool:
        """Verifica si el archivo es válido para procesar."""
        if not archivo:
            return False
        
        # Verificar que tiene nombre de archivo
        if not archivo.filename or archivo.filename.strip() == "":
            return False
        
        # Verificar que tiene contenido
        if hasattr(archivo, 'size'):
            if archivo.size is None or archivo.size == 0:
                return False
        
        # Verificar que el archivo tiene contenido leyendo su posición
        try:
            current_position = archivo.file.tell()
            archivo.file.seek(0, 2)  # Ir al final
            file_size = archivo.file.tell()
            archivo.file.seek(current_position)  # Volver a la posición original
            
            if file_size == 0:
                return False
        except:
            # Si no se puede leer, asumir que no es válido
            return False
        
        return True

    async def ejecutar(
        self,
        placa: str,
        tipo: str,
        marca: str,
        modelo: str,
        color: str,
        usuario: Usuario,
        estado: str = "Activo",
        archivo_foto: Optional[UploadFile] = None
    ) -> Vehiculo:
        
        # 1. Validar y crear tipo de vehículo
        tipo_vehiculo = TipoVehiculo(tipo)
        
        # 2. Validar y crear placa para el tipo específico
        placa_vehiculo = PlacaVehiculo.crear_para_tipo(placa, tipo_vehiculo)
        
        # 3. Verificar que no existe otro vehículo con la misma placa
        if self.repositorio.existe_placa(placa_vehiculo.valor):
            raise ValueError(f"Ya existe un vehículo registrado con la placa '{placa_vehiculo.valor}'")
        
        # 4. Manejo de foto
        ruta_foto = ""
        
        # Solo procesar si el archivo es realmente válido
        if self._es_archivo_valido(archivo_foto):
            try:
                ruta_foto = await self.servicio_archivos.guardar_imagen_vehiculo(
                    archivo_foto, 
                    usuario.numero_documento.valor
                )
            except Exception as e:
                # Si hay error al guardar, usar imagen por defecto (no lanzar error)
                print(f"Advertencia: No se pudo guardar la imagen: {str(e)}")
                ruta_foto = ""
        
        # 5. Crear el vehículo con fecha local de Colombia
        vehiculo = Vehiculo(
            placa=placa_vehiculo,
            tipo=tipo_vehiculo,
            marca=MarcaVehiculo(marca),
            modelo=ModeloVehiculo(modelo),
            color=ColorVehiculo(color),
            foto=FotoVehiculo(ruta_foto),
            estado=EstadoVehiculo(estado),
            usuario=usuario,
            fecha_registro=obtener_fecha_local()
        )
        
        # 6. Guardar en repositorio
        self.repositorio.agregar(vehiculo)
        
        return vehiculo

    def ejecutar_sin_archivo(
        self,
        placa: str,
        tipo: str,
        marca: str,
        modelo: str,
        color: str,
        usuario: Usuario,
        foto_ruta: str = "",
        estado: str = "Activo"
    ) -> Vehiculo:
        """Versión síncrona para cuando no se maneja archivo de subida."""
        
        # 1. Validar y crear tipo de vehículo
        tipo_vehiculo = TipoVehiculo(tipo)
        
        # 2. Validar y crear placa para el tipo específico
        placa_vehiculo = PlacaVehiculo.crear_para_tipo(placa, tipo_vehiculo)
        
        # 3. Verificar que no existe otro vehículo con la misma placa
        if self.repositorio.existe_placa(placa_vehiculo.valor):
            raise ValueError(f"Ya existe un vehículo registrado con la placa '{placa_vehiculo.valor}'")
        
        # 4. Crear el vehículo con fecha local de Colombia
        vehiculo = Vehiculo(
            placa=placa_vehiculo,
            tipo=tipo_vehiculo,
            marca=MarcaVehiculo(marca),
            modelo=ModeloVehiculo(modelo),
            color=ColorVehiculo(color),
            foto=FotoVehiculo(foto_ruta),
            estado=EstadoVehiculo(estado),
            usuario=usuario,
            fecha_registro=obtener_fecha_local()
        )
        
        # 5. Guardar en repositorio
        self.repositorio.agregar(vehiculo)
        
        return vehiculo