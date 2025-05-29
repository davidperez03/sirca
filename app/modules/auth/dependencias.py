from fastapi import Depends, Request
from sqlalchemy.orm import Session
from typing import Optional
from jose import jwt, JWTError

# Configuraciones y dependencias del proyecto
from app.core.config import settings
from app.core.dependencias.dependencias import get_db

# Módulos de autenticación
# Ajustar estas rutas de importación según la estructura real del proyecto
from app.modules.autenticacion.infrastructure.repositorios.repositorio import RepositorioUsuariosBD 
from app.modules.autenticacion.domain.entidades.usuario import Usuario as UsuarioEntidad

class EsquemaUsuarioPlantilla:
    def __init__(self, autenticado: bool = False, nombre: Optional[str] = None, numero_documento: Optional[str] = None, rol: Optional[str] = None):
        self.autenticado = autenticado
        self.nombre = nombre
        self.numero_documento = numero_documento
        self.rol = rol # Añadido por si es útil en las plantillas

async def obtener_datos_usuario_plantilla(
    request: Request,
    db: Session = Depends(get_db)
) -> EsquemaUsuarioPlantilla:
    try:
        token = request.cookies.get("access_token")
        if not token:
            return EsquemaUsuarioPlantilla(autenticado=False)

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        numero_documento: Optional[str] = payload.get("sub")
        
        if not numero_documento:
            # Token válido pero sin 'sub', o 'sub' está vacío.
            # Considerar loguear esta situación.
            return EsquemaUsuarioPlantilla(autenticado=False)

    except JWTError:
        # Token inválido (expirado, malformado, firma incorrecta)
        # Considerar loguear el error específico si es necesario para depuración.
        return EsquemaUsuarioPlantilla(autenticado=False)
    
    # Si llegamos aquí, el token fue decodificado y tenemos un numero_documento.
    # Ahora buscamos al usuario en la BD.
    # Es importante que RepositorioUsuariosBD se importe correctamente.
    # La clase RepositorioUsuariosBD espera 'session' en su __init__.
    repo_usuarios = RepositorioUsuariosBD(session=db) 
    
    # El método en RepositorioUsuariosBD es obtener_por_id
    usuario_entidad = repo_usuarios.obtener_por_id(numero_documento) 

    if usuario_entidad and usuario_entidad.activo:
        # Acceder al atributo .valor de NombrePropio
        nombre_completo = f"{usuario_entidad.nombres.valor} {usuario_entidad.apellidos.valor}"
        return EsquemaUsuarioPlantilla(
            autenticado=True,
            nombre=nombre_completo,
            numero_documento=usuario_entidad.numero_documento.valor, # Acceder al valor del OV
            rol=usuario_entidad.rol.value # Acceder al valor del Enum RolUsuario
        )
    
    # Usuario no encontrado en BD con ese numero_documento, o no está activo.
    # Considerar loguear esta situación.
    return EsquemaUsuarioPlantilla(autenticado=False)
