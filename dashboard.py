import streamlit as st
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MotoFix - Panel Maestro", layout="wide", page_icon="🛠️")

# --- BARRA LATERAL (CONFIGURACIÓN DE CONEXIÓN) ---
st.sidebar.title("🌐 Conexión con el Taller")
# Aquí es donde pegarás la URL de Serveo (ej: https://xxxx.serveousercontent.com)
api_base = st.sidebar.text_input(
    "URL de la API (Serveo/Local)", 
    value="http://localhost:8000",
    help="Pega aquí la URL que te dio la terminal de Serveo"
)
API_URL = api_base.strip("/") # Limpiamos espacios y barras finales

st.sidebar.divider()
st.sidebar.info(f"Conectado a: {API_URL}")

# --- TÍTULO PRINCIPAL ---
st.title("🛠️ Centro de Entrenamiento MotoFix")

tab1, tab2 = st.tabs(["📋 Revisar Clientes", "🧪 Simular y Entrenar IA"])

# --- TAB 1: REVISAR CONSULTAS REALES DE CLIENTES ---
with tab1:
    st.header("Consultas pendientes de usuarios")
    try:
        response = requests.get(f"{API_URL}/pendientes", timeout=10)
        if response.status_code == 200:
            fallas = response.json()
            if not fallas:
                st.success("¡Todo al día! No hay consultas de clientes por revisar.")
            else:
                for f in fallas:
                    with st.expander(f"Falla ID #{f['id']}: {f['descripcion'][:50]}..."):
                        st.write(f"**Usuario dijo:** {f['descripcion']}")
                        st.info(f"**IA respondió:** {f['respuesta_ia']}")
                        
                        nueva_corr = st.text_input("Corrección del mecánico:", key=f"real_{f['id']}")
                        if st.button("Guardar Aprendizaje", key=f"btn_real_{f['id']}"):
                            requests.post(f"{API_URL}/corregir", json={"id_diagnostico": f['id'], "correccion": nueva_corr})
                            st.success("¡Aprendido!")
                            st.rerun()
        else:
            st.error(f"Error de Servidor: {response.status_code}")
    except Exception as e:
        st.error(f"No se pudo conectar a la API. ¿Pegaste la URL de Serveo correctamente? Error: {e}")

# --- TAB 2: SIMULADOR PARA EL MECÁNICO ---
with tab2:
    st.header("🧪 Simulador de Diagnóstico")
    st.write("Escribe una falla para evaluar la precisión de la IA.")
    
    falla_test = st.text_input("Simular falla (ej: Mi moto tiene un ruido metálico al encender):")
    
    if st.button("Probar IA"):
        if falla_test:
            with st.spinner('MotoFix IA está analizando la falla...'):
                try:
                    res = requests.post(
                        f"{API_URL}/diagnosticar", 
                        json={"usuario_id": 999, "descripcion": falla_test},
                        timeout=15
                    )
                    if res.status_code == 200:
                        data = res.json()
                        st.subheader("Resultado de la IA:")
                        st.write(data['diagnostico'])
                        
                        if data.get('necesita_cita'):
                            st.warning("⚠️ RECOMENDACIÓN TÉCNICA: Esta falla requiere revisión en taller.")
                        
                        st.divider()
                        st.info("Si la respuesta requiere ajustes técnicos, búscala en la pestaña 'Revisar Clientes' para entrenar el modelo.")
                    else:
                        st.error(f"Error en la API: {res.text}")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
        else:
            st.warning("Por favor, ingrese una descripción técnica para proceder.")