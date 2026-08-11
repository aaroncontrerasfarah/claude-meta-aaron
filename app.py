import streamlit as st
from groq import Groq
import PyPDF2
import os
from io import BytesIO
from docx import Document
from datetime import datetime

st.set_page_config(page_title="Claude Meta • Aaron - FAST", page_icon="⚡", layout="wide")
st.markdown("""
<style>
    .main { background-color: #FAF9F5; }
    [data-testid="stSidebar"] { background-color: #F0EEE6; }
    .claude-card { background: white; border-radius: 16px; padding: 16px; border: 1px solid #E8E5DD; }
</style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GROQ_API_KEY") if "GROQ_API_KEY" in st.secrets else os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚡ Claude FAST")
    st.caption("No se pega nunca")
    uploaded = st.file_uploader("📄 PDF Matemáticas", type=["pdf","txt"])
    if uploaded:
        try:
            if uploaded.type == "application/pdf":
                reader = PyPDF2.PdfReader(uploaded)
                # Solo primeras 5 páginas para no pegarse
                max_pages = min(5, len(reader.pages))
                text = ""
                for i in range(max_pages):
                    text += (reader.pages[i].extract_text() or "") + "\n"
                st.session_state['pdf_text'] = text[:12000]  # Límite para no pegarse
                st.session_state['pdf_name'] = uploaded.name
                st.success(f"✅ {uploaded.name} - {max_pages} págs leídas (de {len(reader.pages)})")
                st.caption(f"{len(st.session_state['pdf_text'])} caracteres - recortado para velocidad")
                with st.expander("Ver texto"):
                    st.text(st.session_state['pdf_text'][:3000])
            else:
                text = uploaded.read().decode('utf-8')[:12000]
                st.session_state['pdf_text'] = text
                st.success("✅ TXT cargado")
        except Exception as e:
            st.error(f"Error leyendo PDF: {e}")
    
    st.divider()
    if st.button("🗑️ Limpiar"):
        st.session_state.messages = []
        st.session_state.pdf_text = ""
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("¿Qué analizamos, Aaron?")
st.caption("⚡ Modelo ultra rápido - Streaming en vivo - No se pega")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# INPUT QUE NO SE PEGA
st.divider()
pregunta = st.text_input("✍️ Escribe tu pregunta aquí:", placeholder="Ej: Resuelve el ejercicio 3 paso a paso...", key="pregunta_input")

col1, col2, col3, col4 = st.columns(4)
with col1:
    btn_preguntar = st.button("🚀 PREGUNTAR", type="primary", use_container_width=True)
with col2:
    if st.button("📊 Analizar PDF", use_container_width=True):
        pregunta = "Analiza este PDF de matemáticas a fondo: teoría, fórmulas clave y resuelve los ejercicios principales paso a paso con procedimiento completo."
        btn_preguntar = True
with col3:
    if st.button("🧮 Resolver todo", use_container_width=True):
        pregunta = "Resuelve TODOS los ejercicios del PDF paso a paso con desarrollo completo y verificación."
        btn_preguntar = True
with col4:
    if st.button("📝 Resumen largo", use_container_width=True):
        pregunta = "Haz un resumen ejecutivo profundo de mínimo 600 palabras con ideas clave, análisis crítico y conclusiones."
        btn_preguntar = True

if btn_preguntar and pregunta:
    if not client:
        st.error("Falta API KEY")
        st.stop()
    
    pdf_text = st.session_state.get('pdf_text','')
    if not pdf_text:
        st.warning("Primero sube un PDF en la barra izquierda")
    
    st.session_state.messages.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    # Contexto recortado para no pegarse
    contexto = f"PDF {st.session_state.get('pdf_name','')}: {pdf_text[:10000]}\n\nPREGUNTA: {pregunta}" if pdf_text else pregunta

    SYSTEM = """
Eres el mejor profesor de matemáticas de Chile. Fecha 11 ago 2026.
Respuestas LARGAS (mínimo 600 palabras), paso a paso, con fórmulas LaTeX $...$.
Si es ejercicio: Enunciado, Datos, Fórmula, Desarrollo numerado, Resultado, Verificación.
NUNCA digas que sabes hasta 2023. No inventes.
"""

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        try:
            # STREAMING = no se ve pegado, escribe en vivo
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Modelo más rápido del mundo, no se pega
                messages=[{"role": "system", "content": SYSTEM},{"role": "user", "content": contexto}],
                temperature=0.4,
                max_tokens=5000,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Botón Word
            def make_doc():
                doc = Document()
                doc.add_heading('Solución Matemáticas', 1)
                doc.add_paragraph(full_response)
                bio = BytesIO()
                doc.save(bio)
                return bio.getvalue()
            st.download_button("📄 Descargar en WORD", make_doc(), file_name="solucion.docx")
            
        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Si falla, prueba con 'llama-3.1-8b-instant' que es aún más rápido")

                  
