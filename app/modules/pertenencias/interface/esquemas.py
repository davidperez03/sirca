from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PertenenciaCreate(BaseModel):
    nombre: str
    tipo: str
    descripcion: Optional[str] = ""
    serial: Optional[str] = ""
    foto: Optional[str] = ""
    estado: Optional[str] = "Activo"

class PertenenciaRead(BaseModel):
    nombre: str
    tipo: str
    descripcion: Optional[str] = ""
    serial: Optional[str] = ""
    foto: Optional[str] = ""
    estado: str
    usuario_id: str
    fecha_registro: datetime

    @classmethod
    def from_domain(cls, p):
        return cls(
            nombre=p.nombre.valor,
            tipo=p.tipo.value,
            descripcion=p.descripcion.valor,
            serial=p.serial.valor,
            foto=p.foto.valor,
            estado=p.estado.value,
            usuario_id=p.usuario.numero_documento.valor,
            fecha_registro=p.fecha_registro
        )