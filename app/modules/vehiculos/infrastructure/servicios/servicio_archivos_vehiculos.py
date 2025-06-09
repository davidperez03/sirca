"""
Servicio para manejar la subida y gestión de archivos de imágenes de vehículos.
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException

class ServicioArchivosVehiculos:
    def __init__(self):
        self.directorio_base = Path("app/core/resources/media")
        self.directorio_vehiculos = self.directorio_base / "vehiculos"
        self.extensiones_permitidas = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        self.tamaño_maximo = 10 * 1024 * 1024  # 10 MB

        # Crear directorios si no existen
        self.directorio_vehiculos.mkdir(parents=True, exist_ok=True)

    async def guardar_imagen_vehiculo(
        self, 
        archivo: UploadFile, 
        usuario_id: str
    ) -> str:
        """
        Guarda una imagen de vehículo y retorna la ruta relativa.
        """
        # Validaciones básicas
        if not archivo:
            raise HTTPException(status_code=400, detail="No se proporcionó un archivo.")
        
        if not hasattr(archivo, 'filename') or not archivo.filename:
            raise HTTPException(status_code=400, detail="El archivo no tiene nombre válido.")
        
        if archivo.filename.strip() == "":
            raise HTTPException(status_code=400, detail="El nombre del archivo está vacío.")
        
        # Validar extensión
        extension = Path(archivo.filename).suffix.lower()
        if extension not in self.extensiones_permitidas:
            extensiones_str = ', '.join(self.extensiones_permitidas)
            raise HTTPException(
                status_code=400, 
                detail=f"Extensión no permitida. Use: {extensiones_str}"
            )
        
        # Validar tamaño de forma segura
        try:
            # Obtener posición actual
            posicion_inicial = archivo.file.tell()
            
            # Ir al final para obtener tamaño
            archivo.file.seek(0, 2)
            tamaño_archivo = archivo.file.tell()
            
            # Volver a la posición inicial
            archivo.file.seek(posicion_inicial)
            
            if tamaño_archivo == 0:
                raise HTTPException(status_code=400, detail="El archivo está vacío.")
            
            if tamaño_archivo > self.tamaño_maximo:
                tamaño_mb = self.tamaño_maximo / (1024 * 1024)
                raise HTTPException(
                    status_code=400, 
                    detail=f"El archivo es demasiado grande. Máximo: {tamaño_mb}MB"
                )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=400, detail="Error al validar el archivo.")

        # Generar nombre y guardar
        try:
            # Generar nombre único
            nombre_archivo = f"{usuario_id}_{uuid.uuid4().hex}{extension}"
            
            # Crear directorio del usuario si no existe
            directorio_usuario = self.directorio_vehiculos / usuario_id
            directorio_usuario.mkdir(exist_ok=True)
            
            # Ruta completa del archivo
            ruta_archivo = directorio_usuario / nombre_archivo
            
            # Guardar archivo
            archivo.file.seek(0)  # Asegurar que estamos al inicio
            with open(ruta_archivo, "wb") as buffer:
                shutil.copyfileobj(archivo.file, buffer)
            
            # Retornar ruta relativa
            return f"media/vehiculos/{usuario_id}/{nombre_archivo}"
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error al guardar el archivo: {str(e)}"
            )

    def eliminar_imagen(self, ruta_relativa: str) -> bool:
        """Elimina una imagen del sistema de archivos."""
        if not ruta_relativa:
            return True
        
        try:
            ruta_completa = Path("app/core/resources") / ruta_relativa
            if ruta_completa.exists():
                ruta_completa.unlink()
                
                # Intentar eliminar directorio si está vacío
                directorio_padre = ruta_completa.parent
                if directorio_padre != self.directorio_vehiculos:
                    try:
                        directorio_padre.rmdir()  # Solo elimina si está vacío
                    except OSError:
                        pass  # Directorio no vacío, está bien
                
                return True
        except Exception:
            pass
        
        return False

    def obtener_url_publica(self, ruta_relativa: str) -> str:
        """Convierte una ruta relativa en URL pública."""
        if not ruta_relativa:
            return "/static/img/no-vehicle.png"
        
        # Verificar si el archivo existe
        if not self.existe_archivo(ruta_relativa):
            return "/static/img/no-vehicle.png"
        
        return f"/{ruta_relativa}"

    def existe_archivo(self, ruta_relativa: str) -> bool:
        """Verifica si un archivo existe."""
        if not ruta_relativa:
            return True
        ruta_completa = Path("app/core/resources") / ruta_relativa
        return ruta_completa.exists()

    def es_archivo_valido_para_subida(self, archivo: UploadFile) -> tuple[bool, str]:
        """Verifica si un archivo es válido y retorna el motivo si no lo es."""
        if not archivo:
            return False, "No se proporcionó archivo"
        
        if not hasattr(archivo, 'filename') or not archivo.filename:
            return False, "Archivo sin nombre"
        
        if archivo.filename.strip() == "":
            return False, "Nombre de archivo vacío"
        
        # Verificar extensión
        extension = Path(archivo.filename).suffix.lower()
        if extension not in self.extensiones_permitidas:
            return False, f"Extensión no permitida: {extension}"
        
        # Verificar tamaño
        try:
            posicion_inicial = archivo.file.tell()
            archivo.file.seek(0, 2)
            tamaño_archivo = archivo.file.tell()
            archivo.file.seek(posicion_inicial)
            
            if tamaño_archivo == 0:
                return False, "Archivo vacío"
            
            if tamaño_archivo > self.tamaño_maximo:
                return False, "Archivo demasiado grande"
                
        except Exception:
            return False, "Error al leer archivo"
        
        return True, "Archivo válido"