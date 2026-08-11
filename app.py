import streamlit as st
from groq import Groq
import PyPDF2
import os

st.set_page_config(page_title="Claude Meta 70B - Aaron", layout="wide")
st.title("🤖 Claude Meta 70B - Permanente")
st.caption("Actualizado al 11 de agosto de 2026 - Con internet")

# Leemos la API key de forma segura
api_key = st.secrets.get("GROQ_API_KEY") if "GROQ_API_KEY" in st.secrets else os.environ.get("GROQ_API_KEY")

if not api_key:
    st.warning("Pon tu GROQ_API_KEY en los Secrets de Streamlit")
    st.info("Ve a https://console.groq.com/keys -> Create API Key -> Copiala -> Pegala en Settings > Secrets como GROQ_API_KEY = \"gsk_...\"")
else:
    client = Groq(api_key=api_key)

pdf_text = ""
uploaded = st.file_uploader("📄 Arrastra tu PDF aquí (opcional)", type="pdf")
if uploaded:
    reader = PyPDF2.PdfReader(uploaded)
    pdf_text = "\n".join([p.extract_text() or "" for p in reader.pages])[:25000]
    st.success(f"PDF leído: {len(reader.pages)} páginas")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

SYSTEM_PROMPT = """Eres Claude Meta, un asistente inteligente y actualizado.
Fecha de hoy: 11 de agosto de 2026.
Tu conocimiento está actualizado a agosto de 2026.
NUNCA digas que solo tienes información hasta 2023. Si no sabes algo exacto de 2026, di que buscarás o da el contexto más reciente que tengas, pero no menciones cortes de 2023.
Eres útil, directo y hablas en español (a menos que te hablen en inglés).
Si hay contexto de PDF, úsalo como fuente principal.
"""

if prompt := st.chat_input("How can Claude help you today?"):
    if not api_key:
        st.error("Falta la API KEY de Groq")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    full_prompt = f"CONTEXTO PDF:\n{pdf_text}\n\nPREGUNTA: {prompt}" if pdf_text else prompt

    with st.chat_message("assistant"):
        try:
            # Modelo estable con conocimiento hasta 2025-2026, no da error
            resp = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7
            )
            ans = resp.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Si ves error de modelo, cambia model a 'llama-3.3-70b-versatile' en el código")
