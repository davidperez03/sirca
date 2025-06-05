'''
    Servicio para manejar la subida y gestión de archivos de imágenes.
'''
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException

class ServicioArchivos:
    def __init__(self):
        self.directorio_base = Path("app/core/resources/media")
        self.directorio_pertenencias = self.directorio_base / "pertenencias"
        self.extensiones_permitidas = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        self.tamaño_maximo = 10 * 1024 * 1024  # 10 MB

        # Crear directorios si no existen
        self.directorio_pertenencias.mkdir(parents=True, exist_ok=True)

    async def guardar_imagen_pertenencia(
        self, 
        archivo: UploadFile, 
        usuario_id: str
    ) -> str:
        """
        Guarda una imagen de pertenencia y retorna la ruta relativa.
        """
        # Validar archivo
        self._validar_archivo(archivo)

        # Generar nombre único
        extension = Path(archivo.filename).suffix.lower()
        nombre_archivo = f"{usuario_id}_{uuid.uuid4().hex}{extension}"
        
        # Crear directorio del usuario si no existe
        directorio_usuario = self.directorio_pertenencias / usuario_id
        directorio_usuario.mkdir(exist_ok=True)
        
        # Ruta completa del archivo
        ruta_archivo = directorio_usuario / nombre_archivo
        
        try:
            # Guardar archivo
            with open(ruta_archivo, "wb") as buffer:
                shutil.copyfileobj(archivo.file, buffer)
            
            # Retornar ruta relativa
            return f"media/pertenencias/{usuario_id}/{nombre_archivo}"
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error al guardar el archivo: {str(e)}"
            )

    def eliminar_imagen(self, ruta_relativa: str) -> bool:
        """
        Elimina una imagen del sistema de archivos.
        """
        if not ruta_relativa:
            return True
        
        try:
            ruta_completa = Path("app/core/resources") / ruta_relativa
            if ruta_completa.exists():
                ruta_completa.unlink()
                
                # Intentar eliminar directorio si está vacío
                directorio_padre = ruta_completa.parent
                if directorio_padre != self.directorio_pertenencias:
                    try:
                        directorio_padre.rmdir()  # Solo elimina si está vacío
                    except OSError:
                        pass  # Directorio no vacío, está bien
                
                return True
        except Exception:
            pass
        
        return False

    def _validar_archivo(self, archivo: UploadFile) -> None:
        """
        Valida que el archivo cumple con los requisitos.
        """
        if not archivo.filename:
            raise HTTPException(status_code=400, detail="No se proporcionó un archivo.")
        
        # Validar extensión
        extension = Path(archivo.filename).suffix.lower()
        if extension not in self.extensiones_permitidas:
            extensiones_str = ', '.join(self.extensiones_permitidas)
            raise HTTPException(
                status_code=400, 
                detail=f"Extensión no permitida. Use: {extensiones_str}"
            )
        
        # Validar tamaño (FastAPI ya lee el contenido, así que usamos seek)
        archivo.file.seek(0, 2)  # Ir al final del archivo
        tamaño = archivo.file.tell()
        archivo.file.seek(0)  # Volver al inicio
        
        if tamaño > self.tamaño_maximo:
            tamaño_mb = self.tamaño_maximo / (1024 * 1024)
            raise HTTPException(
                status_code=400, 
                detail=f"El archivo es demasiado grande. Máximo: {tamaño_mb}MB"
            )

    def obtener_url_publica(self, ruta_relativa: str) -> str:
        """
        Convierte una ruta relativa en URL pública.
        """
        if not ruta_relativa:
            return "/static/img/no-image.png"
        
        # Verificar si el archivo existe
        if not self.existe_archivo(ruta_relativa):
            return "/static/img/no-image.png"
        
        return f"/{ruta_relativa}"

    def existe_archivo(self, ruta_relativa: str) -> bool:
        """
        Verifica si un archivo existe.
        """
        if not ruta_relativa:
            return True
        ruta_completa = Path("app/core/resources") / ruta_relativa
        return ruta_completa.exists()