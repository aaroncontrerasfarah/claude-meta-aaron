import streamlit as st
from groq import Groq
import PyPDF2
import os
from datetime import datetime
from io import BytesIO
from docx import Document

st.set_page_config(page_title="Claude Meta • Aaron", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

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
</style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GROQ_API_KEY") if "GROQ_API_KEY" in st.secrets else os.environ.get("GROQ_API_KEY")
if api_key:
    client = Groq(api_key=api_key)
else:
    st.sidebar.error("⚠️ Falta GROQ_API_KEY en Secrets")
    client = None

with st.sidebar:
    st.markdown('<div class="title-gradient">Claude Meta</div>', unsafe_allow_html=True)
    st.caption(f"por Aaron • {datetime.now().strftime('%d %b 2026')}")
    st.divider()
    st.markdown("### 📄 Documentos")
    uploaded = st.file_uploader("Arrastra PDF, DOCX, TXT", type=["pdf","docx","txt"], label_visibility="collapsed")

    pdf_text = ""
    if uploaded:
        st.markdown('<div class="claude-card">', unsafe_allow_html=True)
        if uploaded.type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded)
            pdf_text = "\n".join([(p.extract_text() or "") for p in reader.pages])
            st.success(f"✅ PDF: {len(reader.pages)} páginas")
            st.session_state['pdf_text'] = pdf_text
            st.session_state['pdf_name'] = uploaded.name
            with st.expander("👁️ Vista previa"):
                st.text_area("Contenido", pdf_text[:5000], height=250)
        elif uploaded.type == "text/plain":
            pdf_text = uploaded.read().decode('utf-8')
            st.success(f"✅ TXT cargado")
            st.session_state['pdf_text'] = pdf_text
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        pdf_text = st.session_state.get('pdf_text', '')

    st.divider()
    if st.button("🗑️ Limpiar chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("### 📤 Exportar")
    if "messages" in st.session_state and st.session_state.messages:
        chat_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        st.download_button("⬇️ TXT", chat_text, file_name="claude_chat.txt", use_container_width=True)
        def create_word():
            doc = Document()
            doc.add_heading('Conversación Claude Meta - Aaron', 0)
            for m in st.session_state.messages:
                p = doc.add_paragraph()
                run = p.add_run(f"{m['role'].upper()}: "); run.bold = True
                p.add_run(m['content'])
            bio = BytesIO(); doc.save(bio); return bio.getvalue()
        st.download_button("⬇️ WORD", create_word(), file_name="claude_chat.docx", use_container_width=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown('<span class="badge">● ONLINE</span> <span style="margin-left:8px; font-weight:600;">Claude 4 Sonnet • Ago 2026</span>', unsafe_allow_html=True)
st.markdown("## ¿En qué te ayudo hoy, Aaron?")

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🧑‍💻" if m["role"]=="user" else "🤖"):
        st.markdown(m["content"])

prompt = st.chat_input("Escribe tu pregunta, pega código o pide un documento...")

if prompt:
    if not client: st.error("Falta GROQ_API_KEY"); st.stop()
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"): st.markdown(prompt)
    context = f"DOCUMENTO '{st.session_state.get('pdf_name','')}':\n{pdf_text[:20000]}\n\n" if pdf_text else ""
    full_prompt = context + prompt
    SYSTEM = """Eres Claude Meta, asistente de Aaron. Fecha: 11 ago 2026. NUNCA digas que tu info es hasta 2023. NUNCA inventes marcadores. Si te piden código, genera código limpio con ```python. Si te piden Word, estructura profesional. Si hay PDF, úsalo como fuente."""
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Pensando..."):
            resp = client.chat.completions.create(model="openai/gpt-oss-120b", messages=[{"role": "system", "content": SYSTEM},{"role": "user", "content": full_prompt}], temperature=0.3)
            ans = resp.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
