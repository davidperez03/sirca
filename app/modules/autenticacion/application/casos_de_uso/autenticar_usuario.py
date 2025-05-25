'''
    Caso de uso para la autenticación de usuarios.
    Este módulo contiene la función para autenticar un usuario en el sistema.
'''

# Entidades y puertos del dominio
from app.modules.autenticacion.domain.entidades.usuario import Usuario
from app.modules.autenticacion.domain.puertos.repositorio_usuarios import RepositorioUsuarios

# Objetos de valor del dominio
from app.modules.autenticacion.domain.objetos_de_valor.enums.tipo_documento import TipoDocumento
from app.modules.autenticacion.domain.objetos_de_valor.numero_documento import NumeroDocumento

# Infraestructura — verificación de contraseñas
from app.modules.autenticacion.infrastructure.cifrador_contrasena.cifrador import verify_password

def autenticar_usuario(
    repo: RepositorioUsuarios,
    tipo_doc: TipoDocumento,
    valor_doc: str,
    contrasena_plana: str
) -> Usuario:
    # 1) Reconstruir VO de identificación
    numero_vo = NumeroDocumento(tipo_doc, valor_doc)

    # 2) Recuperar entidad
    usuario = repo.obtener_por_id(numero_vo.valor)
    if not usuario:
        raise ValueError("Usuario no encontrado")

    # 3) Verificar contraseña
    if not verify_password(contrasena_plana, usuario.contrasena.hash):
        raise ValueError("Credenciales inválidas")

    return usuario

