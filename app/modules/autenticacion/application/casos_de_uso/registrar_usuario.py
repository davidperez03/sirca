'''
    Caso de uso para registrar un nuevo usuario en el sistema.
'''

# Servicios de autenticación
from app.modules.auth.seguridad import crear_token_activacion

# Entidades de dominio
from app.modules.autenticacion.domain.entidades.usuario import Usuario

# Puertos del dominio
from app.modules.autenticacion.domain.puertos.repositorio_usuarios import RepositorioUsuarios

# Objetos de valor del dominio
from app.modules.autenticacion.domain.objetos_de_valor.enums.tipo_documento import TipoDocumento
from app.modules.autenticacion.domain.objetos_de_valor.enums.rol_usuario import RolUsuario
from app.modules.autenticacion.domain.objetos_de_valor.numero_documento import NumeroDocumento
from app.modules.autenticacion.domain.objetos_de_valor.nombre_propio import NombrePropio
from app.modules.autenticacion.domain.objetos_de_valor.correo_institucional import CorreoInstitucional
from app.modules.autenticacion.domain.objetos_de_valor.contrasena import Contrasena

# Constantes del dominio
from app.modules.autenticacion.domain.constantes.rol_registro import ROLES_PERMITIDOS_REGISTRO

# Servicios de dominio
from app.modules.autenticacion.domain.servicios.validador_contrasena import ValidadorContrasena

# Infraestructura
from app.modules.autenticacion.infrastructure.cifrador_contrasena.cifrador import hash_password

def registrar_usuario(
    repo: RepositorioUsuarios,
    tipo_doc: TipoDocumento,
    valor_doc: str,
    nombres_str: str,
    apellidos_str: str,
    correo_str: str,
    contrasena_plana: str,
    rol: RolUsuario,
) -> Usuario:
    # 1) Reconstruir VOs de la identidad
    numero_vo   = NumeroDocumento(tipo_doc, valor_doc)
    nombres_vo  = NombrePropio(nombres_str)
    apellidos_vo= NombrePropio(apellidos_str)
    correo_vo   = CorreoInstitucional(correo_str)

    # 2) Verificar duplicados
    if repo.obtener_por_id(numero_vo.valor):
        raise ValueError(f"Ya existe el usuario {numero_vo.valor}")
    if repo.obtener_por_correo(correo_vo.valor):
        raise ValueError(f"Ya existe el correo {correo_vo.valor}")
    
    # 2) Verificar el rol
    if rol not in ROLES_PERMITIDOS_REGISTRO:
        raise ValueError("No tienes permiso para registrarte con este rol.")
    
    # 3) Hashear contraseña
    ValidadorContrasena.validar(contrasena_plana)
    hash_        = hash_password(contrasena_plana)
    contrasena_vo= Contrasena(hash_)

    # 4) Crear entidad y persistir (activo=False)
    usuario = Usuario(
        tipo_documento       = tipo_doc,
        numero_documento     = numero_vo,
        nombres              = nombres_vo,
        apellidos            = apellidos_vo,
        correo_institucional = correo_vo,
        contrasena           = contrasena_vo,
        activo               = False,
        rol                  = rol
    )
    repo.guardar(usuario)

    return usuario


