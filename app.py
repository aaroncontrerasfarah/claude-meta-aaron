
import streamlit as st
from groq import Groq
import PyPDF2
import os

st.set_page_config(page_title="Claude Meta 70B - Aaron", layout="wide")
st.title("🤖 Claude Meta 70B - Permanente")

# Leemos la API key de forma segura
api_key = st.secrets.get("GROQ_API_KEY") if "GROQ_API_KEY" in st.secrets else os.environ.get("GROQ_API_KEY")

if not api_key:
    st.warning("Pon tu GROQ_API_KEY en los Secrets de Streamlit (te muestro abajo)")
else:
    client = Groq(api_key=api_key)

pdf_text = ""
uploaded = st.file_uploader("📄 Arrastra tu PDF aquí (opcional)", type="pdf")
if uploaded:
    reader = PyPDF2.PdfReader(uploaded)
    pdf_text = "\n".join([p.extract_text() or "" for p in reader.pages])[:20000]
    st.success(f"PDF leído: {len(reader.pages)} páginas")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("How can Claude help you today?"):
    if not api_key:
        st.error("Falta la API KEY de Groq")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    full_prompt = f"CONTEXTO PDF:\n{pdf_text}\n\nPREGUNTA: {prompt}" if pdf_text else prompt

    with st.chat_message("assistant"):
        resp = client.chat.completions.create(
               model="groq/compound",
            messages=[{"role": "user", "content": full_prompt}]
        )
        ans = resp.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
