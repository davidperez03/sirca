'''
    Módulo de seguridad para autenticación de usuarios mediante cookies.
    Contiene funciones para extraer y validar tokens JWT almacenados en cookies.
'''
# Librerías de terceros
from fastapi import Request
from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError

# Configuración principal
from app.core.config import settings

def obtener_token_cookie(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
        )
    return token

def validar_token_cookie(token: str = Depends(obtener_token_cookie)) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
