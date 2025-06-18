'''
Objeto de valor para el JWT del QR de acceso
'''
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict
from jose import jwt
from app.core.config import settings

@dataclass(frozen=True)
class QRJwt:
    valor: str  # El JWT en sí
    
    def __post_init__(self):
        if not self.valor or len(self.valor) < 50:
            raise ValueError("JWT de QR inválido")
        
        # Validar que sea un JWT válido
        try:
            jwt.decode(self.valor, settings.secret_key, algorithms=[settings.algorithm])
        except Exception:
            raise ValueError("JWT malformado o inválido")
    
    @classmethod
    def crear_nuevo(
        cls,
        usuario_id: str,
        duracion_minutos: int,
        pertenencias: List[Dict] = None,
        vehiculos: List[Dict] = None
    ) -> 'QRJwt':
        """Crea un nuevo JWT para QR de acceso"""
        
        if not 1 <= duracion_minutos <= 60:
            raise ValueError("Duración debe estar entre 1 y 60 minutos")
        
        # Generar ID único para el QR
        qr_id = str(uuid.uuid4())
        
        # Fecha de expiración
        expiracion = datetime.utcnow() + timedelta(minutes=duracion_minutos)
        
        # Payload del JWT
        payload = {
            "sub": usuario_id,  # Usuario
            "qr_id": qr_id,     # ID único del QR
            "exp": expiracion,  # Expiración
            "iat": datetime.utcnow(),  # Emitido en
            "type": "qr_acceso",  # Tipo de token
            "duracion": duracion_minutos,
            "pertenencias": pertenencias or [],
            "vehiculos": vehiculos or [],
            "usado": False
        }
        
        # Generar JWT
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        
        return cls(valor=token)
    
    def decodificar(self) -> Dict:
        """Decodifica el JWT y retorna el payload"""
        try:
            return jwt.decode(self.valor, settings.secret_key, algorithms=[settings.algorithm])
        except Exception as e:
            raise ValueError(f"Error decodificando JWT: {str(e)}")
    
    def obtener_usuario_id(self) -> str:
        """Obtiene el ID del usuario del JWT"""
        payload = self.decodificar()
        return payload.get("sub", "")
    
    def obtener_qr_id(self) -> str:
        """Obtiene el ID único del QR"""
        payload = self.decodificar()
        return payload.get("qr_id", "")
    
    def esta_expirado(self) -> bool:
        """Verifica si el JWT ha expirado"""
        try:
            payload = self.decodificar()
            exp = payload.get("exp")
            if exp:
                return datetime.utcnow().timestamp() > exp
            return True
        except:
            return True
    
    def obtener_pertenencias(self) -> List[Dict]:
        """Obtiene las pertenencias incluidas en el QR"""
        payload = self.decodificar()
        return payload.get("pertenencias", [])
    
    def obtener_vehiculos(self) -> List[Dict]:
        """Obtiene los vehículos incluidos en el QR"""
        payload = self.decodificar()
        return payload.get("vehiculos", [])