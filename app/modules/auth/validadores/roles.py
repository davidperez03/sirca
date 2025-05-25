from fastapi import Request
from functools import wraps
from jose import jwt
from app.core.config import settings
from app.modules.autenticacion.domain.objetos_de_valor.enums.rol_usuario import RolUsuario
from fastapi import HTTPException, status

# Decorador para validar el rol requerido en un endpoint, API REST para integración externa
def rol_requerido_jwt(roles: list[RolUsuario]):
    def decorator(endpoint):
        @wraps(endpoint)
        async def wrapper(request: Request, *args, **kwargs):
            token = request.headers.get("Authorization")
            if not token or not token.startswith("Bearer "):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no encontrado.")
            token = token.replace("Bearer ", "")

            try:
                payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
                rol = payload.get("rol")
                if rol not in [r.value for r in roles]:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rol no autorizado.")
            except Exception:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")

            return await endpoint(request, *args, **kwargs)
        return wrapper
    return decorator

# Decorador para validar el rol requerido en un endpoint, API REST para integración interna
# Este decorador se utiliza para validar el rol de un usuario a través de un token almacenado en una cookie.
def rol_requerido_cookie(*roles_requeridos):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            token = request.cookies.get("access_token")
            if not token:
                raise HTTPException(status_code=401, detail="Token no encontrado.")

            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            rol = payload.get("rol")
            if rol not in roles_requeridos:
                raise HTTPException(status_code=403, detail="Acceso no autorizado, Volverrrrr.")
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
