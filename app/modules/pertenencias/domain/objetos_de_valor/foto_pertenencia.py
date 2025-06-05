'''
    Objeto de valor para la foto de la pertenencia.
    Maneja solo archivos locales, no URLs externas.
'''
import re
import os
from dataclasses import dataclass
from pathlib import Path

EXTENSIONES_PERMITIDAS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
TAMAÑO_MAXIMO_MB = 10  # 10 MB máximo por archivo

@dataclass(frozen=True)
class FotoPertenencia:
    valor: str  # Ruta relativa del archivo

    def __post_init__(self):
        limpio = self.valor.strip() if self.valor else ""
        
        # Permitir valor vacío (foto opcional)
        if not limpio:
            object.__setattr__(self, "valor", "")
            return
        
        # Validar que sea una ruta de archivo local válida
        if not self._es_ruta_local_valida(limpio):
            raise ValueError("La foto debe ser una ruta de archivo local válida.")
        
        # Validar extensión
        extension = Path(limpio).suffix.lower()
        if extension not in EXTENSIONES_PERMITIDAS:
            extensiones_str = ', '.join(EXTENSIONES_PERMITIDAS)
            raise ValueError(f"La foto debe tener una extensión válida: {extensiones_str}")
        
        # Normalizar la ruta
        ruta_normalizada = self._normalizar_ruta(limpio)
        object.__setattr__(self, "valor", ruta_normalizada)

    def _es_ruta_local_valida(self, ruta: str) -> bool:
        """Valida que sea una ruta local y no una URL."""
        # No debe ser una URL
        if re.match(r'^https?://', ruta, re.IGNORECASE):
            return False
        
        # Debe tener una estructura de archivo válida
        if not re.match(r'^[\w\-/\\\.\s]+\.(jpg|jpeg|png|webp|gif)$', ruta, re.IGNORECASE):
            return False
        
        return True

    def _normalizar_ruta(self, ruta: str) -> str:
        """Normaliza la ruta del archivo."""
        # Convertir barras invertidas a barras normales
        ruta_normalizada = ruta.replace('\\', '/')
        
        # Remover barras dobles
        ruta_normalizada = re.sub(r'/+', '/', ruta_normalizada)
        
        # Si no empieza con media/, agregarlo
        if not ruta_normalizada.startswith('media/'):
            if ruta_normalizada.startswith('/'):
                ruta_normalizada = ruta_normalizada[1:]
            ruta_normalizada = f"media/{ruta_normalizada}"
        
        return ruta_normalizada

    def obtener_ruta_completa(self) -> str:
        """Obtiene la ruta completa del archivo."""
        if not self.valor:
            return ""
        return f"app/core/resources/{self.valor}"

    def existe_archivo(self) -> bool:
        """Verifica si el archivo existe físicamente."""
        if not self.valor:
            return True  # Foto opcional
        ruta_completa = self.obtener_ruta_completa()
        return os.path.exists(ruta_completa)

    def obtener_url_publica(self) -> str:
        """Obtiene la URL pública para mostrar en templates."""
        if not self.valor:
            return "/static/img/no-image.png"  # Imagen por defecto
        
        # Verificar si el archivo existe físicamente
        if not self.existe_archivo():
            return "/static/img/no-image.png"  # Imagen por defecto si no existe
        
        return f"/{self.valor}"