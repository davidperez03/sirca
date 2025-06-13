import uuid
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass(frozen=True)
class CodigoQR:
    valor: str
    
    def __post_init__(self):
        if not self.valor or len(self.valor) < 20:
            raise ValueError("Código QR inválido")
        object.__setattr__(self, "valor", self.valor.upper())
    
    @classmethod
    def generar_nuevo(cls, usuario_id: str) -> 'CodigoQR':
        """Genera un código QR único y seguro"""
        timestamp = str(int(datetime.now().timestamp()))
        random_uuid = str(uuid.uuid4())
        data = f"{usuario_id}:{timestamp}:{random_uuid}"
        hash_value = hashlib.sha256(data.encode()).hexdigest()[:32]
        return cls(f"SIRCA-{hash_value}")