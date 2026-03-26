import sqlite3

def crear_base_datos():
    conexion = sqlite3.connect('motoia_aprendizaje.db')
    cursor = conexion.cursor()
    # Tabla para guardar: Falla descrita, Lo que dijo la IA, y Corrección del Mecánico
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diagnosticos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion_usuario TEXT,
            respuesta_ia TEXT,
            correccion_mecanico TEXT,
            es_correcta BOOLEAN
        )
    ''')
    conexion.commit()
    conexion.close()

crear_base_datos()
print("Base de datos de aprendizaje lista.")