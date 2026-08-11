import streamlit as st
from groq import Groq
import os

st.set_page_config(page_title="Claude Aaron FAST", page_icon="⚡", layout="centered")

api_key = st.secrets.get("GROQ_API_KEY") if "GROQ_API_KEY" in st.secrets else os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("⚡ Claude Aaron - Instant")
st.caption("Carga en 2s | Modelo 8B instantáneo")

# PDF opcional pero cargado solo si lo usas
pdf_text = ""
with st.sidebar:
    st.markdown("### 📄 PDF (opcional)")
    uploaded = st.file_uploader("Sube PDF", type=["pdf"], label_visibility="collapsed")
    if uploaded:
        import PyPDF2
        reader = PyPDF2.PdfReader(uploaded)
        pdf_text = ""
        for i in range(min(3, len(reader.pages))):
            pdf_text += reader.pages[i].extract_text() or ""
        pdf_text = pdf_text[:6000]
        st.success(f"PDF {len(reader.pages)} págs | usando 3 primeras")
    if st.button("Limpiar chat"):
        st.session_state.messages = []
        st.rerun()

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# INPUT RAPIDO
prompt = st.chat_input("Pregunta algo...")

if prompt:
    if not client:
        st.error("Falta GROQ_API_KEY en Secrets")
        st.stop()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    contexto = f"PDF: {pdf_text[:5000]}\n\nPregunta: {prompt}" if pdf_text else prompt
    
    SYSTEM = """
Eres Claude, profesor de matemáticas experto. Fecha: 11 ago 2026.
Respuestas profundas mínimo 500 palabras, paso a paso, con fórmulas LaTeX.
Estructura: Resumen, Desarrollo detallado numerado, Conclusión.
Nunca digas corte 2023. No inventes.
"""

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full = ""
        try:
            stream = client.chat.completions.create(
                model="llama-3.1-8b-instant",  # EL MÁS RÁPIDO DE TODOS - 500 tokens/s
                messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": contexto}],
                temperature=0.5,
                max_tokens=4000,
                stream=True
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    full += delta
                    placeholder.markdown(full + "▌")
            placeholder.markdown(full)
            st.session_state.messages.append({"role": "assistant", "content": full})
        except Exception as e:
            st.error(str(e))

