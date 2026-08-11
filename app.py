import streamlit as st
from groq import Groq
import PyPDF2
import os
from datetime import datetime
from io import BytesIO
from docx import Document

st.set_page_config(page_title="Claude Meta • Aaron - FIX", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    .main { background-color: #FAF9F5; }
    [data-testid="stSidebar"] { background-color: #F0EEE6; }
    .claude-card { background: white; border-radius: 16px; padding: 20px; border: 1px solid #E8E5DD; box-shadow: 0 2px 12px rgba(0,0,0,0.04); margin-bottom: 16px; }
    .badge { background: #D4A574; color: white; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    .title-gradient { background: linear-gradient(90deg, #D4A574 0%, #8B5E34 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 32px; }
</style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GROQ_API_KEY") if "GROQ_API_KEY" in st.secrets else os.environ.get("GROQ_API_KEY")
if api_key:
    client = Groq(api_key=api_key)
else:
    client = None
    st.error("⚠️ Falta GROQ_API_KEY en Secrets")

with st.sidebar:
    st.markdown('<div class="title-gradient">Claude Meta</div>', unsafe_allow_html=True)
    st.caption("FIX Botón - Matemáticas")
    st.divider()
    uploaded = st.file_uploader("📄 Sube tu PDF de matemáticas", type=["pdf","txt"])
    pdf_text = st.session_state.get('pdf_text','')
    if uploaded:
        if uploaded.type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded)
            pdf_text = "\n".join([(p.extract_text() or "") for p in reader.pages])
            st.session_state['pdf_text'] = pdf_text
            st.session_state['pdf_name'] = uploaded.name
            st.success(f"✅ PDF cargado: {len(reader.pages)} páginas")
        else:
            pdf_text = uploaded.read().decode('utf-8')
            st.session_state['pdf_text'] = pdf_text
    st.divider()
    if st.button("🗑️ Limpiar chat"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown('<span class="badge">● ONLINE - FIX</span> <b>Claude Análisis Matemático Profundo</b>', unsafe_allow_html=True)

# Historial
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🧑‍💻" if m["role"]=="user" else "🤖"):
        st.markdown(m["content"])

# --- ZONA DE PREGUNTA QUE NUNCA SE BLOQUEA ---
st.divider()
st.markdown("### ✍️ Haz tu pregunta (funciona siempre)")

col1, col2 = st.columns([4,1])
with col1:
    user_question = st.text_area("Pregunta:", placeholder="Ej: Explica paso a paso los ejercicios del PDF, resuelve el ejercicio 3 con todo el procedimiento...", height=100, key="q_input")
with col2:
    st.write("")
    st.write("")
    preguntar_btn = st.button("🚀 PREGUNTAR", type="primary", use_container_width=True)
    st.caption("Este botón nunca se bloquea")

# Sugerencias rápidas
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("📊 Analizar todo el PDF", use_container_width=True):
        user_question = "Haz un análisis profundo y exhaustivo de todo el PDF de matemáticas: explica la teoría, resuelve cada ejercicio paso a paso con procedimiento completo, justifica cada paso."
        preguntar_btn = True
with c2:
    if st.button("🧮 Resolver ejercicios", use_container_width=True):
        user_question = "Resuelve todos los ejercicios del PDF de matemáticas paso a paso, con procedimiento completo, fórmulas usadas y verificación del resultado."
        preguntar_btn = True
with c3:
    if st.button("📝 Crear guía Word", use_container_width=True):
        user_question = "Crea una guía de estudio en formato de informe basada en el PDF, con teoría, ejemplos resueltos y ejercicios propuestos."
        preguntar_btn = True

if preguntar_btn and user_question:
    if not client:
        st.error("Falta API KEY")
        st.stop()
    if not st.session_state.get('pdf_text'):
        st.warning("Sube primero un PDF en la barra lateral izquierda")

    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_question)

    pdf_text = st.session_state.get('pdf_text','')
    context = f"DOCUMENTO MATEMÁTICO '{st.session_state.get('pdf_name','')}' CONTENIDO:\n{pdf_text[:35000]}\n\n" if pdf_text else ""
    full_prompt = context + f"\nPREGUNTA DEL USUARIO: {user_question}"

    SYSTEM = """
Eres Claude Meta, el mejor profesor de matemáticas de Chile, experto en enseñanza universitaria.
Fecha: 11 agosto 2026. Español.

MODO MATEMÁTICAS PROFUNDO - OBLIGATORIO:
- Respuestas de MÍNIMO 700 palabras.
- Si es un ejercicio: muestra ENUNCIADO, DATOS, FÓRMULA, DESARROLLO PASO A PASO numerado, RESULTADO y VERIFICACIÓN.
- Usa LaTeX para fórmulas: $x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}$ para inline y $$...$$ para bloques.
- Explica el POR QUÉ de cada paso, no solo el cómo.
- Si hay varios ejercicios, resuelve uno por uno con títulos.
- Estructura con: Resumen, Teoría Clave, Desarrollo Detallado, Conclusión.
- NUNCA digas que tu info llega hasta 2023.
- NUNCA inventes datos. Si el PDF no se lee bien, di qué parte no se lee.
- Sé didáctico, como si le explicaras a un alumno que quiere aprender de verdad.
"""

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Resolviendo paso a paso..."):
            try:
                resp = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[{"role": "system", "content": SYSTEM},{"role": "user", "content": full_prompt}],
                    temperature=0.4,
                    max_tokens=7000
                )
                ans = resp.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                
                # Botón Word
                def doc_from_ans():
                    doc = Document()
                    doc.add_heading('Análisis Matemático - Claude Meta', 1)
                    doc.add_paragraph(ans)
                    bio = BytesIO()
                    doc.save(bio)
                    return bio.getvalue()
                st.download_button("📄 Descargar en WORD", doc_from_ans(), file_name="solucion_matematicas.docx")
                
            except Exception as e:
                st.error(f"Error: {e}")
