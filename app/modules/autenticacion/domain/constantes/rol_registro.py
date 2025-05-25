from app.modules.autenticacion.domain.objetos_de_valor.enums.rol_usuario import RolUsuario

ROLES_PERMITIDOS_REGISTRO = [
    RolUsuario.FUNCIONARIO,
    RolUsuario.CONTRATISTA,
    RolUsuario.APRENDIZ,
    RolUsuario.INSTRUCTOR,
]
