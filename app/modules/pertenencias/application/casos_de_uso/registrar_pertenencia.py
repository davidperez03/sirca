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
        
        # 4. Procesar foto si se proporciona
        ruta_foto = ""
        if archivo_foto:
            try:
                ruta_foto = await self.servicio_archivos.guardar_imagen_pertenencia(
                    archivo_foto, 
                    usuario.numero_documento.valor
                )
            except Exception as e:
                raise ValueError(f"Error al procesar la imagen: {str(e)}")
        
        # 5. Crear la pertenencia con fecha local de Colombia
        pertenencia = Pertenencia(
            nombre=NombrePertenencia(nombre),
            tipo=tipo_pertenencia,
            descripcion=DescripcionPertenencia(descripcion),
            serial=serial_pertenencia,
            foto=FotoPertenencia(ruta_foto),
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
            foto=FotoPertenencia(foto_ruta),
            estado=EstadoPertenencia(estado),
            usuario=usuario,
            fecha_registro=obtener_fecha_local()
        )
        
        # 5. Guardar en repositorio
        self.repositorio.agregar(pertenencia)
        
        return pertenencia