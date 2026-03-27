from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from google import genai
import time

app = FastAPI(title="MotoFix API")
client = genai.Client(api_key="api")

# Modelos de datos
class ConsultaMoto(BaseModel):
    usuario_id: int = 1
    descripcion: str

class CorreccionMecanico(BaseModel):
    id_diagnostico: int
    correccion: str

# --- LÓGICA DE BASE DE DATOS ---
def inicializar_db():
    conn = sqlite3.connect('motoia_aprendizaje.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diagnosticos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion_usuario TEXT,
            respuesta_ia TEXT,
            correccion_mecanico TEXT,
            es_correcta INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def buscar_aprendizaje_previo(consulta_usuario):
    """Busca en la DB correcciones validadas para alimentar a la IA."""
    conn = sqlite3.connect('motoia_aprendizaje.db')
    cursor = conn.cursor()
    # Buscamos solo lo que el mecánico ya corrigió/validó
    cursor.execute('SELECT descripcion_usuario, correccion_mecanico FROM diagnosticos WHERE es_correcta = 1 AND correccion_mecanico IS NOT NULL')
    registros = cursor.fetchall()
    conn.close()
    
    if registros:
        contexto = "\nNOTAS DEL MECÁNICO EN CARACAS (USA ESTO PARA TU RESPUESTA):\n"
        for desc_ant, corr_ant in registros:
            contexto += f"- Para la falla '{desc_ant}', la solución real fue: {corr_ant}\n"
        return contexto
    return ""

inicializar_db()

# --- ENDPOINTS ---

@app.get("/")
def inicio():
    return {"mensaje": "MotoFix API activa en Caracas"}

@app.post("/diagnosticar")
def diagnosticar(datos: ConsultaMoto):
    # --- PASO 1: FILTRO DE RELEVANCIA (GUARDRAIL) ---
    prompt_filtro = f"""
    Eres un clasificador de contenido. Responde ÚNICAMENTE con la palabra 'SI' o 'NO'.
    ¿La siguiente consulta está relacionada estrictamente con mecánica de motos, fallas, repuestos o mantenimiento de motocicletas?
    Consulta: "{datos.descripcion}"
    """
    
    try:
        # Usamos una llamada rápida para validar
        check = client.models.generate_content(
            model="gemini-flash-latest", 
            contents=prompt_filtro
        )
        
        # Si la respuesta no es un "SI" rotundo, rechazamos sin guardar en DB
        if "SI" not in check.text.upper():
            return {
                "diagnostico": "Lo siento, soy un especialista en motos. No puedo ayudarte con temas fuera de la mecánica o el mantenimiento de motocicletas.",
                "modelo_usado": "filtro-seguridad",
                "necesita_cita": False
            }
            
    except Exception as e:
        print(f"Error en filtro: {e}") # Si falla el filtro por cuota, podrías dejarlo pasar o bloquearlo

    # --- PASO 2: DIAGNÓSTICO NORMAL (Solo si pasó el filtro) ---
    modelos_disponibles = ["gemini-2.0-flash", "gemini-flash-latest"]
    aprendizaje_previo = buscar_aprendizaje_previo(datos.descripcion)

    for modelo_nombre in modelos_disponibles:
        try:
            prompt= (
                f"""
                Usted es MotoFix IA, un asistente técnico especializado en motocicletas en Caracas.
                
                INSTRUCCIONES DE RESPUESTA:
                1. DIAGNÓSTICO: Analice la falla y mencione brevemente las causas técnicas probables.
                2. BREVEDAD: Mantenga la respuesta en un máximo de 3 a 4 líneas de texto.
                3. PROTOCOLO PROFESIONAL: 
                - Si la falla compromete la seguridad o el motor interno, responda: "Debido a la complejidad técnica, se recomienda una inspección profesional inmediata. ¿Desea agendar una cita con nuestro especialista en [Zona de Caracas]?"
                - Si el usuario muestra interés en la revisión, instrúyalo a escribir 'AGENDAR'.
                
                CONTEXTO TÉCNICO PREVIO:
                {aprendizaje_previo}
                """
            )

            response = client.models.generate_content(
                model=modelo_nombre, 
                contents=prompt
            )
            respuesta_texto = response.text

            # GUARDADO EN DB: Solo llegamos aquí si la consulta es de motos
            conn = sqlite3.connect('motoia_aprendizaje.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO diagnosticos (descripcion_usuario, respuesta_ia) VALUES (?, ?)', 
                           (datos.descripcion, respuesta_texto))
            conn.commit()
            conn.close()

            palabras_cita = ["agendar", "revisión", "taller", "cita", "mecánico"]
            cita_necesaria = any(p in respuesta_texto.lower() for p in palabras_cita)

            return {
                "diagnostico": respuesta_texto, 
                "modelo_usado": modelo_nombre,
                "necesita_cita": cita_necesaria
            }

        except Exception as e:
            if "429" in str(e):
                continue
            raise HTTPException(status_code=500, detail=str(e))
    
    raise HTTPException(status_code=429, detail="Cuota agotada. Intenta en 1 minuto.")

@app.get("/pendientes")
def obtener_pendientes():
    conn = sqlite3.connect('motoia_aprendizaje.db')
    cursor = conn.cursor()
    # Traemos ID, descripción del usuario y lo que dijo la IA
    cursor.execute('SELECT id, descripcion_usuario, respuesta_ia FROM diagnosticos WHERE es_correcta = 0')
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "descripcion": f[1], "respuesta_ia": f[2]} for f in filas]

@app.post("/corregir")
def corregir_falla(datos: CorreccionMecanico):
    """Permite al mecánico entrenar a la IA desde la interfaz"""
    conn = sqlite3.connect('motoia_aprendizaje.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE diagnosticos 
        SET correccion_mecanico = ?, es_correcta = 1 
        WHERE id = ?
    ''', (datos.correccion, datos.id_diagnostico))
    conn.commit()
    conn.close()
    return {"mensaje": "Aprendizaje guardado correctamente"}
