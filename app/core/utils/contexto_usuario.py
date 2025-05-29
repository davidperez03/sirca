from fastapi import Request
from sqlalchemy.orm import Session
from app.modules.auth.seguridad import decodificar_token
from app.modules.auth.blacklist import esta_en_blacklist
from app.modules.autenticacion.infrastructure.repositorios.repositorio import RepositorioUsuariosBD

def obtener_contexto_usuario(request: Request, db: Session) -> dict:
    """Retorna el contexto del usuario autenticado basado en la cookie de sesión"""
    context = {
        "usuario_autenticado": False,
        "usuario_nombre": None,
        "usuario_id": None
    }

    token = request.cookies.get("access_token")
    if token:
        try:
            if not esta_en_blacklist(token):
                payload = decodificar_token(token)
                usuario_id = payload.get("sub")
                if usuario_id:
                    repo = RepositorioUsuariosBD(db)
                    usuario = repo.obtener_por_id(usuario_id)
                    if usuario and usuario.activo:
                        context.update({
                            "usuario_autenticado": True,
                            "usuario_nombre": f"{usuario.nombres.valor} {usuario.apellidos.valor}",
                            "usuario_id": usuario_id
                        })
        except Exception:
            pass

    return context
