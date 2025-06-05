from datetime import datetime
from typing import Optional
from fastapi import UploadFile
from app.core.utils.fechas import obtener_fecha_local
from app.modules.pertenencias.domain.entidades.pertenencia import Pertenencia
from app.modules.pertenencias.domain.objetos_de_valor.nombre_pertenencia import NombrePertenencia
from app.modules.pertenencias.domain.objetos_de_valor.tipo_pertenencia import TipoPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.descripcion_pertenencia import DescripcionPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.serial_pertenencia import SerialPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.foto_pertenencia import FotoPertenencia
from app.modules.pertenencias.domain.objetos_de_valor.estado_pertenencia import EstadoPertenencia
from app.modules.pertenencias.domain.puertos.repositorio_pertenencias import RepositorioPertenencias
from app.modules.pertenencias.infrastructure.servicios.servicio_archivos import ServicioArchivos
from app.modules.autenticacion.domain.entidades.usuario import Usuario

class RegistrarPertenencia:
    def __init__(self, repositorio: RepositorioPertenencias):
        self.repositorio = repositorio
        self.servicio_archivos = ServicioArchivos()

    def _es_archivo_valido(self, archivo: Optional[UploadFile]) -> bool:
        """
        ✅ NUEVA FUNCIÓN: Verifica si el archivo es válido para procesar
        """
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
        nombre: str,
        tipo: str,
        descripcion: str,
        serial: str,
        usuario: Usuario,
        estado: str = "Activo",
        archivo_foto: Optional[UploadFile] = None
    ) -> Pertenencia:
        
        # 1. Validar y crear tipo de pertenencia
        tipo_pertenencia = TipoPertenencia(tipo)
        
        # 2. Validar y crear serial (con validación de obligatoriedad)
        serial_pertenencia = SerialPertenencia.crear_para_tipo(serial, tipo_pertenencia)
        
        # 3. Verificar que no existe otra pertenencia con el mismo serial (si tiene serial)
        if serial_pertenencia.valor:
            pertenencia_existente = self.repositorio.obtener_por_serial(serial_pertenencia.valor)
            if pertenencia_existente:
                raise ValueError(f"Ya existe una pertenencia con el serial '{serial_pertenencia.valor}'")
        
        # 4. ✅ MANEJO MEJORADO DE FOTO
        ruta_foto = ""
        
        # Solo procesar si el archivo es realmente válido
        if self._es_archivo_valido(archivo_foto):
            try:
                ruta_foto = await self.servicio_archivos.guardar_imagen_pertenencia(
                    archivo_foto, 
                    usuario.numero_documento.valor
                )
            except Exception as e:
                # Si hay error al guardar, usar imagen por defecto (no lanzar error)
                print(f"Advertencia: No se pudo guardar la imagen: {str(e)}")
                ruta_foto = ""
        
        # ✅ Si ruta_foto está vacía, FotoPertenencia automáticamente usará imagen por defecto
        
        # 5. Crear la pertenencia con fecha local de Colombia
        pertenencia = Pertenencia(
            nombre=NombrePertenencia(nombre),
            tipo=tipo_pertenencia,
            descripcion=DescripcionPertenencia(descripcion),
            serial=serial_pertenencia,
            foto=FotoPertenencia(ruta_foto),  # ✅ Puede ser vacía = imagen por defecto
            estado=EstadoPertenencia(estado),
            usuario=usuario,
            fecha_registro=obtener_fecha_local()
        )
        
        # 6. Guardar en repositorio
        self.repositorio.agregar(pertenencia)
        
        return pertenencia

    def ejecutar_sin_archivo(
        self,
        nombre: str,
        tipo: str,
        descripcion: str,
        serial: str,
        usuario: Usuario,
        foto_ruta: str = "",
        estado: str = "Activo"
    ) -> Pertenencia:
        """
        Versión síncrona para cuando no se maneja archivo de subida.
        """
        # 1. Validar y crear tipo de pertenencia
        tipo_pertenencia = TipoPertenencia(tipo)
        
        # 2. Validar y crear serial (con validación de obligatoriedad)
        serial_pertenencia = SerialPertenencia.crear_para_tipo(serial, tipo_pertenencia)
        
        # 3. Verificar que no existe otra pertenencia con el mismo serial (si tiene serial)
        if serial_pertenencia.valor:
            pertenencia_existente = self.repositorio.obtener_por_serial(serial_pertenencia.valor)
            if pertenencia_existente:
                raise ValueError(f"Ya existe una pertenencia con el serial '{serial_pertenencia.valor}'")
        
        # 4. Crear la pertenencia con fecha local de Colombia
        pertenencia = Pertenencia(
            nombre=NombrePertenencia(nombre),
            tipo=tipo_pertenencia,
            descripcion=DescripcionPertenencia(descripcion),
            serial=serial_pertenencia,
            foto=FotoPertenencia(foto_ruta),  # ✅ Puede ser vacía
            estado=EstadoPertenencia(estado),
            usuario=usuario,
            fecha_registro=obtener_fecha_local()
        )
        
        # 5. Guardar en repositorio
        self.repositorio.agregar(pertenencia)
        
        return pertenencia