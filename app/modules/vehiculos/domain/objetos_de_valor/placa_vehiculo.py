"""
Objeto de valor para la placa de vehículo según normativa colombiana.
Motocicletas: ABC12 o ABC12D
Automóviles: ABC123
"""
import re
from dataclasses import dataclass
from typing import Optional
from app.modules.vehiculos.domain.objetos_de_valor.tipo_vehiculo import TipoVehiculo

# Patrones para placas según tipo de vehículo
PATRON_MOTO_5 = r"^[A-Z]{3}[0-9]{2}$"        # ABC12
PATRON_MOTO_6 = r"^[A-Z]{3}[0-9]{2}[A-Z]$"   # ABC12D
PATRON_CARRO = r"^[A-Z]{3}[0-9]{3}$"          # ABC123

# Placas prohibidas o reservadas
PLACAS_PROHIBIDAS = {
    "AAA000", "BBB000", "CCC000", "DDD000", "EEE000",
    "FFF000", "GGG000", "HHH000", "III000", "JJJ000",
    "TEST00", "ADMIN0", "NULL00", "DEMO00"
}

@dataclass(frozen=True)
class PlacaVehiculo:
    valor: str
    tipo_vehiculo: Optional[TipoVehiculo] = None

    def __post_init__(self):
        limpio = self.valor.strip().upper() if self.valor else ""
        
        if not limpio:
            raise ValueError("La placa es obligatoria")
        
        if len(limpio) < 5 or len(limpio) > 6:
            raise ValueError("La placa debe tener 5 o 6 caracteres")
        
        if limpio in PLACAS_PROHIBIDAS:
            raise ValueError("Placa no permitida o reservada")
        
        # Validar formato según tipo si se proporciona
        if self.tipo_vehiculo:
            if not self._validar_formato_segun_tipo(limpio, self.tipo_vehiculo):
                formato_esperado = self._obtener_formato_esperado(self.tipo_vehiculo)
                raise ValueError(f"Formato de placa inválido para {self.tipo_vehiculo.value}. Formato esperado: {formato_esperado}")
        else:
            # Si no se proporciona tipo, validar que al menos tenga un formato válido
            if not self._es_formato_valido(limpio):
                raise ValueError("Formato de placa inválido. Use: ABC12, ABC12D (motos) o ABC123 (carros)")
        
        object.__setattr__(self, "valor", limpio)

    def _validar_formato_segun_tipo(self, placa: str, tipo: TipoVehiculo) -> bool:
        """Valida que la placa tenga el formato correcto según el tipo de vehículo."""
        if tipo == TipoVehiculo.MOTOCICLETA:
            return re.match(PATRON_MOTO_5, placa) or re.match(PATRON_MOTO_6, placa)
        elif tipo == TipoVehiculo.AUTOMOVIL:
            return re.match(PATRON_CARRO, placa) is not None
        return False

    def _es_formato_valido(self, placa: str) -> bool:
        """Verifica si la placa tiene algún formato válido."""
        return (re.match(PATRON_MOTO_5, placa) or 
                re.match(PATRON_MOTO_6, placa) or 
                re.match(PATRON_CARRO, placa))

    def _obtener_formato_esperado(self, tipo: TipoVehiculo) -> str:
        """Retorna el formato esperado según el tipo."""
        if tipo == TipoVehiculo.MOTOCICLETA:
            return "ABC12 o ABC12D"
        elif tipo == TipoVehiculo.AUTOMOVIL:
            return "ABC123"
        return "Formato no definido"

    def determinar_tipo_por_formato(self) -> Optional[TipoVehiculo]:
        """Determina el tipo de vehículo basándose en el formato de la placa."""
        if re.match(PATRON_MOTO_5, self.valor) or re.match(PATRON_MOTO_6, self.valor):
            return TipoVehiculo.MOTOCICLETA
        elif re.match(PATRON_CARRO, self.valor):
            return TipoVehiculo.AUTOMOVIL
        return None

    @classmethod
    def crear_para_tipo(cls, valor: str, tipo_vehiculo: TipoVehiculo) -> 'PlacaVehiculo':
        """Factory method para crear placa con validación específica de tipo."""
        return cls(valor=valor, tipo_vehiculo=tipo_vehiculo)