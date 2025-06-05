'''
    Objeto de valor mejorado para el serial o identificador único de una pertenencia.
    Ahora maneja la validación de serial obligatorio según el tipo de pertenencia.
'''
import re
from dataclasses import dataclass
from typing import Optional
from app.modules.pertenencias.domain.objetos_de_valor.tipo_pertenencia import TipoPertenencia

PALABRAS_PROHIBIDAS = {"admin", "root", "null", "test", "serial", "default", "undefined", "none"}
PATRONES_PROHIBIDOS = [r"1234+", r"0000+", r"1111+", r"abcd+", r"qwer+", r"aaaa+"]

@dataclass(frozen=True)
class SerialPertenencia:
    valor: str
    es_obligatorio: bool = False

    def __post_init__(self):
        limpio = self.valor.strip() if self.valor else ""
        
        # Si es obligatorio y está vacío, error
        if self.es_obligatorio and not limpio:
            raise ValueError("El serial es obligatorio para este tipo de pertenencia.")
        
        # Si no es obligatorio y está vacío, permitir
        if not self.es_obligatorio and not limpio:
            object.__setattr__(self, "valor", "")
            return
        
        # Si tiene valor, validar formato
        if limpio:
            if not re.fullmatch(r"[A-Za-z0-9\-]{4,30}", limpio):
                raise ValueError("El serial debe tener entre 4 y 30 caracteres alfanuméricos o guiones.")
            
            if limpio.lower() in PALABRAS_PROHIBIDAS:
                raise ValueError("El serial contiene una palabra prohibida.")
            
            if len(set(limpio.lower())) <= 2 and len(limpio) > 4:
                raise ValueError("El serial tiene muy poca variación de caracteres.")
            
            # Verificar patrones prohibidos
            for patron in PATRONES_PROHIBIDOS:
                if re.search(patron, limpio.lower()):
                    raise ValueError("El serial contiene un patrón demasiado simple o común.")
            
            # Convertir a mayúsculas para consistencia
            limpio = limpio.upper()
        
        object.__setattr__(self, "valor", limpio)

    @classmethod
    def crear_para_tipo(cls, valor: str, tipo_pertenencia: TipoPertenencia) -> 'SerialPertenencia':
        """Factory method para crear serial según el tipo de pertenencia."""
        es_obligatorio = TipoPertenencia.requiere_serial_obligatorio(tipo_pertenencia)
        return cls(valor=valor, es_obligatorio=es_obligatorio)