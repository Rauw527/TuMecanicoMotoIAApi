import streamlit as st
import requests

# Si lo subes a la nube, aquí pondrás la URL pública de tu API
API_URL = "http://localhost:8000" 

st.set_page_config(page_title="MotoFix - Panel Maestro", layout="wide", page_icon="🛠️")

st.title("🛠️ Centro de Entrenamiento MotoFix")

# Creamos pestañas para organizar el trabajo
tab1, tab2 = st.tabs(["📋 Revisar Clientes", "🧪 Simular y Entrenar IA"])

# --- TAB 1: REVISAR CONSULTAS REALES DE CLIENTES ---
with tab1:
    st.header("Consultas pendientes de usuarios")
    try:
        response = requests.get(f"{API_URL}/pendientes")
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
    except:
        st.error("Error: ¿Encendiste la API con uvicorn?")

# --- TAB 2: SIMULADOR PARA EL MECÁNICO ---
with tab2:
    st.header("🧪 Simulador de Diagnóstico")
    st.write("Escribe una falla que conozcas para ver si la IA responde correctamente.")
    
    falla_test = st.text_input("Simular falla (ej: Mi Empire bota humo azul):")
    
    if st.button("Probar IA"):
        if falla_test:
            with st.spinner('La IA está analizando...'):
                res = requests.post(f"{API_URL}/diagnosticar", json={"usuario_id": 999, "descripcion": falla_test})
                if res.status_code == 200:
                    data = res.json()
                    st.subheader("Resultado de la IA:")
                    st.write(data['diagnostico'])
                    
                    if data['necesita_cita']:
                        st.warning("⚠️ La IA detectó que esto requiere CITA.")
                    
                    st.divider()
                    st.write("¿La respuesta fue mala? Corrígela aquí mismo para entrenarla:")
                    # Nota: Para corregir una simulación, la API debe haberla guardado antes.
                    # El mecánico solo tiene que ir a la Tab 1 para validarla formalmente.
                    st.info("Si no te gustó, búscala en la pestaña 'Revisar Clientes' y dale la respuesta correcta.")
        else:
            st.warning("Escribe algo para probar.")