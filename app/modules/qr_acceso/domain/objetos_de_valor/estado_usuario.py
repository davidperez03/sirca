'''
Objeto de valor para el estado del usuario en el sistema de acceso
'''
from enum import Enum

class EstadoUsuario(str, Enum):
    """Estados posibles de un usuario en el sistema de acceso"""
    FUERA = "FUERA"           # Usuario está fuera de las instalaciones
    DENTRO = "DENTRO"         # Usuario está dentro de las instalaciones
    BLOQUEADO = "BLOQUEADO"   # Usuario está bloqueado (no puede ingresar/salir)
    
    def siguiente_movimiento_permitido(self) -> str:
        """Retorna el siguiente tipo de movimiento permitido"""
        if self == EstadoUsuario.FUERA:
            return "INGRESO"
        elif self == EstadoUsuario.DENTRO:
            return "SALIDA"
        else:  # BLOQUEADO
            raise ValueError("Usuario bloqueado no puede realizar movimientos")
    
    def puede_generar_qr(self) -> bool:
        """Verifica si el usuario puede generar un QR en este estado"""
        return self != EstadoUsuario.BLOQUEADO
    
    @classmethod
    def desde_ultimo_movimiento(cls, ultimo_movimiento: str) -> 'EstadoUsuario':
        """Determina el estado basado en el último movimiento"""
        if not ultimo_movimiento:
            return cls.FUERA  # Primera vez
        
        if ultimo_movimiento == "INGRESO":
            return cls.DENTRO
        elif ultimo_movimiento == "SALIDA":
            return cls.FUERA
        else:
            return cls.BLOQUEADO