'''
    Caso de uso para obtener un nuevo usuario en el sistema.
'''

# Biblioteca estándar
from typing import Optional

# Entidades del dominio
from app.modules.autenticacion.domain.entidades.usuario import Usuario

# Puertos del dominio
from app.modules.autenticacion.domain.puertos.repositorio_usuarios import RepositorioUsuarios

# Objetos de valor del dominio
from app.modules.autenticacion.domain.objetos_de_valor.enums.tipo_documento import TipoDocumento
from app.modules.autenticacion.domain.objetos_de_valor.numero_documento import NumeroDocumento

def obtener_usuario(
    repo: RepositorioUsuarios,
    tipo_doc: TipoDocumento,
    valor_doc: str
) -> Optional[Usuario]:
    numero_vo = NumeroDocumento(tipo_doc, valor_doc)
    return repo.obtener_por_id(numero_vo.valor)