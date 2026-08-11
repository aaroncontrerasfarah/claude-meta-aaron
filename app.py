import streamlit as st
from groq import Groq
import PyPDF2
import os
from datetime import datetime
from io import BytesIO
from docx import Document
from docx.shared import Pt

st.set_page_config(page_title="Claude Meta • Aaron - PRO Deep", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #FAF9F5; }
    [data-testid="stSidebar"] { background-color: #F0EEE6; border-right: 1px solid #E8E5DD; }
    .claude-card {
        background: white; border-radius: 16px; padding: 20px;
        border: 1px solid #E8E5DD; box-shadow: 0 2px 12px rgba(0,0,0,0.04); margin-bottom: 16px;
    }
    .badge { background: #D4A574; color: white; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    .title-gradient {
        background: linear-gradient(90deg, #D4A574 0%, #8B5E34 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 800; font-size: 32px;
    }
    .stChatMessage { border-radius: 16px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

# --- API KEY ---
api_key = st.secrets.get("GROQ_API_KEY") if "GROQ_API_KEY" in st.secrets else os.environ.get("GROQ_API_KEY")
if api_key:
    client = Groq(api_key=api_key)
else:
    st.sidebar.error("⚠️ Falta GROQ_API_KEY en Secrets de Streamlit")
    client = None

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="title-gradient">Claude Meta</div>', unsafe_allow_html=True)
    st.caption(f"por Aaron • Deep Analysis • {datetime.now().strftime('%d %b 2026')}")
    st.divider()
    
    st.markdown("### 📄 Documentos")
    uploaded = st.file_uploader("Arrastra PDF, TXT", type=["pdf","txt"], label_visibility="collapsed")
    
    pdf_text = st.session_state.get('pdf_text', '')
    if uploaded:
        if uploaded.type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded)
            pdf_text = "\n".join([(p.extract_text() or "") for p in reader.pages])
            st.session_state['pdf_text'] = pdf_text
            st.session_state['pdf_name'] = uploaded.name
            st.success(f"✅ PDF: {len(reader.pages)} págs | {len(pdf_text)} chars")
            with st.expander("👁️ Vista previa (5000 chars)"):
                st.text_area("Contenido", pdf_text[:5000], height=300)
        else:
            pdf_text = uploaded.read().decode('utf-8')
            st.session_state['pdf_text'] = pdf_text
            st.session_state['pdf_name'] = uploaded.name
            st.success(f"✅ TXT: {len(pdf_text)} chars")

    st.divider()
    st.markdown("### 🎛️ Modo de respuesta")
    profundidad = st.select_slider("Profundidad", options=["Corta", "Normal", "Profunda", "Análisis Experto"], value="Análisis Experto")
    st.session_state['profundidad'] = profundidad
    
    st.divider()
    if st.button("🗑️ Limpiar chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("### 📤 Exportar conversación")
    if "messages" in st.session_state and st.session_state.messages:
        chat_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        st.download_button("⬇️ TXT", chat_text, file_name="claude_chat.txt", use_container_width=True)
        def create_word():
            doc = Document()
            doc.add_heading('Conversación Claude Meta - Aaron - Análisis Profundo', 0)
            doc.add_paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Modo: {st.session_state.get('profundidad')}")
            if st.session_state.get('pdf_name'):
                doc.add_paragraph(f"Documento base: {st.session_state['pdf_name']}")
            doc.add_paragraph("")
            for m in st.session_state.messages:
                p = doc.add_paragraph()
                run = p.add_run(f"{m['role'].upper()}: ")
                run.bold = True
                p.add_run(m['content'])
            bio = BytesIO()
            doc.save(bio)
            return bio.getvalue()
        st.download_button("⬇️ WORD (.docx)", create_word(), file_name="claude_chat.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

# --- MAIN ---
if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown('<span class="badge">● ONLINE - MODO DEEP</span> <span style="margin-left:8px; font-weight:600;">Claude 4 Sonnet • Análisis Experto • Ago 2026</span>', unsafe_allow_html=True)
st.markdown("## ¿Qué analizamos hoy, Aaron?")

if not st.session_state.messages:
    st.markdown('<div class="claude-card">', unsafe_allow_html=True)
    st.markdown("**Prueba modo experto:**")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📊 Análisis profundo PDF", use_container_width=True):
            st.session_state['suggest'] = "Haz un análisis profundo y exhaustivo de mi PDF: resumen ejecutivo, ideas clave explicadas, análisis crítico, conexiones teóricas y conclusión con recomendaciones. Mínimo 600 palabras."
    with c2:
        if st.button("💻 Código comentado", use_container_width=True):
            st.session_state['suggest'] = "Genera código en Python bien comentado y luego explícame línea por línea qué hace cada parte y por qué."
    with c3:
        if st.button("📝 Informe Word largo", use_container_width=True):
            st.session_state['suggest'] = "Crea un informe formal largo y profundo basado en el documento, con introducción, marco teórico, desarrollo, análisis crítico, conclusiones y referencias."
    st.markdown('</div>', unsafe_allow_html=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🧑‍💻" if m["role"]=="user" else "🤖"):
        st.markdown(m["content"])

prompt_input = st.session_state.pop('suggest', None)
prompt = st.chat_input("Pide un análisis profundo, código explicado, informe en Word...") or prompt_input

if prompt:
    if not client:
        st.error("Falta GROQ_API_KEY")
        st.stop()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    context = f"DOCUMENTO '{st.session_state.get('pdf_name','')}' COMPLETO:\n{pdf_text[:30000]}\n\n" if pdf_text else ""
    full_prompt = context + prompt

    PROFUNDIDAD = st.session_state.get('profundidad', 'Análisis Experto')
    
    SYSTEM = f"""
Eres Claude Meta, el analista más profundo del mundo, mentor de Aaron Contreras Farah.
Fecha: 11 agosto 2026. Estás actualizado. Hablas en español.

MODO ACTUAL: {PROFUNDIDAD}
- Si es "Corta": 150 palabras.
- Si es "Normal": 300 palabras.
- Si es "Profunda": 500+ palabras con estructura.
- Si es "Análisis Experto": MÍNIMO 700 palabras, estructura obligatoria, tablas, citas del texto, análisis crítico. NUNCA menos de 600 palabras.

ESTRUCTURA OBLIGATORIA PARA ANALIZAR TEXTOS/PDF (cuando el modo es Profunda o Análisis Experto):
Debes responder EXACTAMENTE con estas secciones con markdown:

### 1. 📌 Resumen Ejecutivo
3-4 párrafos que expliquen de qué trata realmente el documento, no solo qué dice.

### 2. 💡 Ideas Clave (7-10 puntos)
Lista cada idea y explica con 2-3 líneas por qué es importante.

### 3. 🔍 Análisis Crítico
- Fortalezas del texto
- Debilidades / vacíos / contradicciones
- Sesgos o supuestos ocultos

### 4. 🔗 Conexiones y Contexto
Relaciona con autores, teorías, contexto chileno/latinoamericano actual (2026) o tu conocimiento.

### 5. ✅ Conclusión y Recomendaciones Prácticas
Qué harías tú con esta información.

### 6. 📊 Tabla / Esquema
Crea una tabla comparativa o un mapa conceptual en markdown.

REGLAS INQUEBRANTABLES:
- NUNCA digas "solo tengo info hasta 2023". Tu corte es agosto 2026.
- NUNCA inventes marcadores de fútbol, noticias o resultados. Si no tienes el dato verificado, di "No tengo ese dato verificado".
- Si te piden código: primero el bloque ```python completo y funcional, luego explica cada bloque línea por línea.
- Si te piden Word: estructura con H1, H2, bullets, listo para exportar.
- Sé visual: usa negritas, tablas, emojis moderados.
- Profundidad sobre brevedad. Aaron odia respuestas cortas.
"""

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner(f"Analizando en modo {PROFUNDIDAD}..."):
            try:
                resp = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.55,
                    max_tokens=7000,
                    top_p=0.9
                )
                ans = resp.choices[0].message.content
                st.markdown(ans)
                
                # Botones para generar docs
                c1, c2 = st.columns(2)
                with c1:
                    def doc_from_ans():
                        doc = Document()
                        doc.add_heading(f'Análisis {PROFUNDIDAD} - Claude Meta', 1)
                        doc.add_paragraph(f"Documento: {st.session_state.get('pdf_name','N/A')} | Fecha: {datetime.now().strftime('%d/%m/%Y')}")
                        doc.add_paragraph(ans)
                        bio = BytesIO()
                        doc.save(bio)
                        return bio.getvalue()
                    st.download_button("📄 Descargar esta respuesta en WORD", doc_from_ans(), file_name="analisis_profundo.docx", key=f"w_{len(st.session_state.messages)}", use_container_width=True)
                
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Si da error de tokens, el PDF es muy largo. Prueba con un PDF más corto o divide la pregunta.")
