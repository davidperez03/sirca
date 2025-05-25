# borrar_todo_sqlite.py

import sqlite3

# Ruta de tu base de datos
DATABASE_PATH = "./sirca.db"

def borrar_todo():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Apagar claves foráneas temporalmente (evitar errores de dependencia)
    cursor.execute("PRAGMA foreign_keys = OFF;")

    # Obtener todas las tablas de la base de datos
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = cursor.fetchall()

    # Borrar datos de cada tabla
    for tabla in tablas:
        tabla_nombre = tabla[0]
        if tabla_nombre == "sqlite_sequence":  # sistema interno de autoincremento
            continue
        cursor.execute(f"DELETE FROM {tabla_nombre};")
        print(f"Tabla '{tabla_nombre}' limpiada.")

    # Activar de nuevo claves foráneas
    cursor.execute("PRAGMA foreign_keys = ON;")

    conn.commit()
    conn.close()
    print("✅ Base de datos limpiada con éxito.")

if __name__ == "__main__":
    borrar_todo()
