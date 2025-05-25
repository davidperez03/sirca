'''
    servicio para validar y generar contraseñas seguras.
    Este servicio se encarga de verificar que una contraseña cumpla con ciertos criterios de seguridad,
    como longitud mínima, presencia de caracteres especiales, y ausencia de patrones comunes.
'''

import re
import bcrypt

class ValidadorContrasena:
    @staticmethod
    def validar(texto_plano: str):
        valor = texto_plano.strip()

        if not valor:
            raise ValueError("La contraseña no puede estar vacía ni contener solo espacios.")

        if len(valor) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        if len(valor) > 64:
            raise ValueError("La contraseña no puede superar 64 caracteres.")

        if not re.search(r'[A-Z]', valor):
            raise ValueError("Debe tener al menos una letra mayúscula.")
        if not re.search(r'[a-z]', valor):
            raise ValueError("Debe tener al menos una letra minúscula.")
        if not re.search(r'[0-9]', valor):
            raise ValueError("Debe tener al menos un número.")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>_\-+=;]', valor):
            raise ValueError("Debe tener al menos un carácter especial.")
        if re.search(r'\s', valor):
            raise ValueError("No debe contener espacios.")
        if re.search(r'(.)\1{4,}', valor):
            raise ValueError("No puede repetir caracteres más de 4 veces.")
        if any(p in valor.lower() for p in ["1234", "abcd", "password", "qwerty", "1111", "0000"]):
            raise ValueError("No puede contener patrones comunes.")

    @staticmethod
    def generar_hash(texto_plano: str) -> str:
        ValidadorContrasena.validar(texto_plano)
        hashed = bcrypt.hashpw(texto_plano.encode(), bcrypt.gensalt())
        return hashed.decode()
