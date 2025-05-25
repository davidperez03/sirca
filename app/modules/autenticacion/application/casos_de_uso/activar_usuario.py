'''
    Caso de uso para activar un usuario.
    Este módulo contiene la función para activar un usuario en el sistema.
    Decodifica el JWT de activación, valida caducidad y activa al usuario en BD. 
    Devuelve el numero_documentoo lanza ValueError con el motivo del fallo.
'''

# Puertos del dominio
from app.modules.autenticacion.domain.puertos.repositorio_usuarios import RepositorioUsuarios

# Servicios de autenticación
from app.modules.auth.seguridad import verificar_token_activacion

def activar_usuario(
    repo: RepositorioUsuarios,
    token: str,
) -> str:
    # 1) Decodifica y valida firma/expiración
    try:
        user_id = verificar_token_activacion(token)
    except ValueError as e:
        raise ValueError(str(e))

    # 2) Trae la entidad y chequea estado
    usuario = repo.obtener_por_id(user_id)
    if not usuario:
        raise ValueError("Usuario no encontrado.")
    if usuario.activo:
        raise ValueError("Cuenta ya activada.")

    # 3) Activa y persiste
    usuario.activo = True
    repo.actualizar(usuario)

    return usuario.numero_documento.valor
