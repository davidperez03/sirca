from enum import Enum

class RolUsuario(str, Enum):
    SUPERADMINISTRADOR = "Superadministrador"
    ADMINISTRADOR = "Administrador"
    FUNCIONARIO = "Funcionario"
    CONTRATISTA = "Contratista"
    APRENDIZ = "Aprendiz"
    INSTRUCTOR = "Instructor"
    OPERATIVO = "Personal operativo"
    APRENDIZ_APOYO = "Aprendiz Apoyo"
    VIGILANTE = "Vigilante"
