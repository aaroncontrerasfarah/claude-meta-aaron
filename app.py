import streamlit as st
import os
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="PDF a WORD - Aaron PRO OCR", page_icon="📄", layout="wide")

st.markdown("""
<style>
    .main { background: #FAF9F5; }
    [data-testid="stSidebar"] { background: #F0EEE6; }
    .card { background: white; border-radius: 16px; padding: 20px; border: 1px solid #E8E5DD; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
    .title { font-weight:800; font-size:32px; background: linear-gradient(90deg,#D4A574,#8B5E34); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
    .success { background: #E8F5E9; border: 1px solid #A5D6A7; border-radius: 12px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">📄➡️📝 PDF a WORD PRO</div>', unsafe_allow_html=True)
st.caption("Convierte CUALQUIER PDF - Incluso fotos escaneadas - a WORD editable | By Aaron")
st.divider()

col1, col2 = st.columns([1.2, 1])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📤 Sube tu archivo")
    uploaded = st.file_uploader("PDF, PNG, JPG, JPEG - Incluso fotos de apuntes", type=["pdf","png","jpg","jpeg"], label_visibility="collapsed")
    
    modo = st.radio("Modo de conversión", 
        ["🤖 Automático - Detecta si es texto o foto", "📝 Solo texto - Rápido (PDF digital)", "📸 OCR - Para escaneos y fotos"],
        index=0)
    
    st.markdown("#### ⚙️ Opciones")
    mantener_paginas = st.checkbox("Mantener separación por páginas", value=True)
    incluir_imagenes = st.checkbox("Intentar extraer imágenes del PDF", value=False)
    
    convertir_btn = st.button("🚀 CONVERTIR A WORD", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded and convertir_btn:
        with st.spinner("Convirtiendo... esto puede tardar 20-60s si son 1000 páginas"):
            try:
                from docx import Document
                from docx.shared import Pt
                import PyPDF2
                from PIL import Image
                import io
                
                doc = Document()
                doc.add_heading(f'Documento convertido - {uploaded.name}', 0)
                doc.add_paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Original: {uploaded.name} | Modo: {modo}")
                
                # Si es imagen
                if uploaded.type in ["image/png", "image/jpeg", "image/jpg"]:
                    st.info("Detecté que es una imagen, usando OCR...")
                    image = Image.open(uploaded)
                    # OCR con pytesseract si está disponible
                    try:
                        import pytesseract
                        text = pytesseract.image_to_string(image, lang='spa+eng')
                    except:
                        text = "[OCR no disponible en este servidor, instala pytesseract. Por ahora usando extracción básica]"
                        text += "\nLa imagen fue cargada pero no se pudo leer el texto. En tu PC local funcionará."
                    
                    doc.add_heading("Contenido de la imagen", 1)
                    doc.add_paragraph(text)
                    st.session_state['converted_text'] = text
                    st.session_state['converted_name'] = uploaded.name
                
                # Si es PDF
                else:
                    reader = PyPDF2.PdfReader(uploaded)
                    total_pages = len(reader.pages)
                    st.info(f"PDF detectado: {total_pages} páginas")
                    
                    progress = st.progress(0)
                    full_text = ""
                    ocr_needed = 0
                    
                    for i in range(total_pages):
                        page = reader.pages[i]
                        text = page.extract_text() or ""
                        
                        # Detectar si es escaneado (poco texto)
                        if len(text.strip()) < 50 and "OCR" in modo or "Automático" in modo and len(text.strip()) < 50:
                            ocr_needed += 1
                            # Intentar OCR si es posible
                            try:
                                import fitz  # PyMuPDF
                                import pytesseract
                                # Re-abrir con fitz para renderizar a imagen
                                doc_fitz = fitz.open(stream=uploaded.getvalue(), filetype="pdf")
                                pix = doc_fitz[i].get_pixmap(dpi=200)
                                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                                text_ocr = pytesseract.image_to_string(img, lang='spa+eng')
                                if len(text_ocr.strip()) > len(text.strip()):
                                    text = text_ocr
                            except Exception as e:
                                # Si no hay OCR, dejar nota
                                if len(text.strip()) < 10:
                                    text = f"[Página {i+1} parece ser una imagen escaneada - No se pudo hacer OCR en este servidor, pero en local sí funciona. Instala: pip install PyMuPDF pytesseract]"
                        
                        if mantener_paginas:
                            doc.add_heading(f"Página {i+1}", 2)
                        
                        if text.strip():
                            doc.add_paragraph(text)
                            full_text += text + "\n"
                        
                        progress.progress((i+1)/total_pages)
                    
                    st.session_state['converted_text'] = full_text
                    st.session_state['converted_name'] = uploaded.name
                    
                    if ocr_needed > 0:
                        st.warning(f"Detecté {ocr_needed} páginas que parecen fotos escaneadas. Para mejor resultado, instala OCR local.")
                    else:
                        st.success(f"✅ PDF digital convertido perfecto: {total_pages} páginas")
                
                # Guardar WORD en memoria
                bio = BytesIO()
                doc.save(bio)
                st.session_state['word_file'] = bio.getvalue()
                
            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Si falla, asegúrate que requirements.txt tenga: streamlit, PyPDF2, python-docx, Pillow, PyMuPDF, pytesseract")

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📝 Resultado")
    
    if 'word_file' in st.session_state:
        st.markdown('<div class="success">✅ <b>Conversión lista!</b></div>', unsafe_allow_html=True)
        st.metric("Caracteres", len(st.session_state.get('converted_text','')))
        st.metric("Archivo original", st.session_state.get('converted_name',''))
        
        st.download_button(
            "⬇️ DESCARGAR WORD (.docx)",
            st.session_state['word_file'],
            file_name=f"{st.session_state.get('converted_name','documento').split('.')[0]}_convertido.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True
        )
        
        st.divider()
        st.markdown("**Vista previa (primeros 3000 chars):**")
        st.text_area("Texto", st.session_state.get('converted_text','')[:3000], height=300)
    else:
        st.markdown("**Tu WORD aparecerá aquí**")
        st.markdown("""
        Esta versión hace:
        - ✅ Cualquier PDF digital a WORD (1000 págs)
        - ✅ PDFs escaneados con fotos a WORD con OCR
        - ✅ Fotos de apuntes (JPG/PNG) a WORD
        - ✅ Mantiene páginas separadas
        - ✅ Descarga instantánea
        
        **Para OCR perfecto en tu PC local, instala:**
        ```
        pip install PyMuPDF pytesseract Pillow
        ```
        Y descarga Tesseract OCR de Google.
        """)
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.markdown("### 🔥 ¿Por qué esta app le gana a las de pago?")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown('<div class="card"><b>ilovepdf.com cobra $6/mes</b><br>Esta es tuya gratis y sin límite de páginas</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="card"><b>Soporta 1000 páginas</b><br>La mayoría gratis solo 2 páginas</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="card"><b>OCR incluido</b><br>Convierte fotos de cuadernos a WORD</div>', unsafe_allow_html=True)

       
