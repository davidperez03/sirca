from typing import Optional
from fastapi import UploadFile
from app.modules.pertenencias.domain.entidades.pertenencia import Pertenencia
from app.modules.pertenencias.domain.objetos_de_valor.nombre_pertenencia import NombrePertenencia
from app.modules.pertenencias.domain.objetos_de_valor.tipo_pertenencia import TipoPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.descripcion_pertenencia import DescripcionPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.serial_pertenencia import SerialPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.foto_pertenencia import FotoPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.estado_pertenencia import EstadoPertenencia
from app.modules.pertenencias.domain.puertos.repositorio_pertenencias import RepositorioPertenencias
from app.modules.pertenencias.infrastructure.servicios.servicio_archivos import ServicioArchivos

class ActualizarPertenencia:
    def __init__(self, repositorio: RepositorioPertenencias):
        self.repositorio = repositorio
        self.servicio_archivos = ServicioArchivos()

    async def ejecutar(
        self,
        id_pertenencia: int,
        nombre: Optional[str] = None,
        tipo: Optional[str] = None,
        descripcion: Optional[str] = None,
        nuevo_serial: Optional[str] = None,
        estado: Optional[str] = None,
        archivo_foto: Optional[UploadFile] = None,
        eliminar_foto: bool = False
    ) -> Pertenencia:
        
        # 1. Obtener pertenencia existente
        pertenencia = self.repositorio.obtener_por_id(id_pertenencia)
        if not pertenencia:
            raise ValueError("Pertenencia no encontrada")
        
        # 2. Actualizar campos si se proporcionan
        if nombre is not None:
            pertenencia.nombre = NombrePertenencia(nombre)
        
        if tipo is not None:
            nuevo_tipo = TipoPertenencia(tipo)
            pertenencia.tipo = nuevo_tipo
            
            # Si cambió el tipo, revalidar el serial
            if nuevo_serial is not None:
                pertenencia.serial = SerialPertenencia.crear_para_tipo(nuevo_serial, nuevo_tipo)
            else:
                # Revalidar serial actual con el nuevo tipo
                pertenencia.serial = SerialPertenencia.crear_para_tipo(
                    pertenencia.serial.valor, nuevo_tipo
                )
        
        if descripcion is not None:
            pertenencia.descripcion = DescripcionPertenencia(descripcion)
        
        if nuevo_serial is not None and tipo is None:
            # Si solo se cambia el serial, usar el tipo actual
            pertenencia.serial = SerialPertenencia.crear_para_tipo(nuevo_serial, pertenencia.tipo)
        
        if estado is not None:
            pertenencia.estado = EstadoPertenencia(estado)
        
        # 3. Manejar foto
        if eliminar_foto:
            # Eliminar foto actual
            if pertenencia.foto.valor:
                self.servicio_archivos.eliminar_imagen(pertenencia.foto.valor)
            pertenencia.foto = FotoPertenencia("")
        
        elif archivo_foto:
            # Eliminar foto anterior si existe
            if pertenencia.foto.valor:
                self.servicio_archivos.eliminar_imagen(pertenencia.foto.valor)
            
            # Guardar nueva foto
            try:
                nueva_ruta = await self.servicio_archivos.guardar_imagen_pertenencia(
                    archivo_foto,
                    pertenencia.usuario.numero_documento.valor
                )
                pertenencia.foto = FotoPertenencia(nueva_ruta)
            except Exception as e:
                raise ValueError(f"Error al procesar la imagen: {str(e)}")
        
        # 4. Verificar serial único si se cambió
        if (nuevo_serial is not None and nuevo_serial != pertenencia.serial.valor and 
            nuevo_serial.strip()):
            existente = self.repositorio.obtener_por_serial(nuevo_serial)
            if existente and existente.id != pertenencia.id:
                raise ValueError(f"Ya existe una pertenencia con el serial '{nuevo_serial}'")
        
        # 5. Actualizar en repositorio
        self.repositorio.actualizar(pertenencia)
        
        return pertenencia

    def ejecutar_sin_archivo(
        self,
        id_pertenencia: int,
        nombre: Optional[str] = None,
        tipo: Optional[str] = None,
        descripcion: Optional[str] = None,
        nuevo_serial: Optional[str] = None,
        estado: Optional[str] = None,
        foto_ruta: Optional[str] = None,
        eliminar_foto: bool = False
    ) -> Pertenencia:
        """
        Versión síncrona para cuando no se maneja archivo de subida.
        """
        # 1. Obtener pertenencia existente
        pertenencia = self.repositorio.obtener_por_id(id_pertenencia)
        if not pertenencia:
            raise ValueError("Pertenencia no encontrada")
        
        # 2. Actualizar campos básicos
        if nombre is not None:
            pertenencia.nombre = NombrePertenencia(nombre)
        
        if tipo is not None:
            nuevo_tipo = TipoPertenencia(tipo)
            pertenencia.tipo = nuevo_tipo
            
            # Revalidar serial con el nuevo tipo
            if nuevo_serial is not None:
                pertenencia.serial = SerialPertenencia.crear_para_tipo(nuevo_serial, nuevo_tipo)
            else:
                pertenencia.serial = SerialPertenencia.crear_para_tipo(
                    pertenencia.serial.valor, nuevo_tipo
                )
        
        if descripcion is not None:
            pertenencia.descripcion = DescripcionPertenencia(descripcion)
        
        if nuevo_serial is not None and tipo is None:
            pertenencia.serial = SerialPertenencia.crear_para_tipo(nuevo_serial, pertenencia.tipo)
        
        if estado is not None:
            pertenencia.estado = EstadoPertenencia(estado)
        
        # 3. Manejar foto
        if eliminar_foto:
            if pertenencia.foto.valor:
                self.servicio_archivos.eliminar_imagen(pertenencia.foto.valor)
            pertenencia.foto = FotoPertenencia("")
        elif foto_ruta is not None:
            pertenencia.foto = FotoPertenencia(foto_ruta)
        
        # 4. Verificar serial único
        if (nuevo_serial is not None and nuevo_serial != pertenencia.serial.valor and 
            nuevo_serial.strip()):
            existente = self.repositorio.obtener_por_serial(nuevo_serial)
            if existente and existente.id != pertenencia.id:
                raise ValueError(f"Ya existe una pertenencia con el serial '{nuevo_serial}'")
        
        # 5. Actualizar
        self.repositorio.actualizar(pertenencia)
        
        return pertenencia