'''
    Modulo para cifrar contrasenas
    El modulo utiliza la libreria bcrypt para realizar el cifrado y la verificacion de contrasenas.
    La libreria bcrypt es una implementacion de hashing de contrasenas que utiliza el algoritmo Blowfish.
    El resultado es un hash que se puede almacenar en la base de datos.
    El hash es irreversible, lo que significa que no se puede recuperar la contrasena original a partir del hash.
    El hash se puede utilizar para verificar si una contrasena proporcionada coincide con la contrasena original.
    El modulo incluye funciones para cifrar una contrasena y para verificar una contrasena proporcionada contra un hash almacenado.
'''

import bcrypt

def hash_password(password: str) -> str:
    """
    Hash the password using bcrypt with a generated salt.
    Returns the hash as a UTF-8 string.
    """
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    # Decode to string for storage
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a plain-text password against the stored bcrypt hash.
    """
    # bcrypt.checkpw returns True if passwords match
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
