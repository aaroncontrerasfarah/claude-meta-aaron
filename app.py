import streamlit as st
import re
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="PDF FOTOS a WORD - FIXED", page_icon="📸", layout="wide")

st.markdown("""
<style>
    .main { background: #FAF9F5; }
    [data-testid="stSidebar"] { background: #F0EEE6; }
    .card { background: white; border-radius: 16px; padding: 20px; border: 1px solid #E8E5DD; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
    .title { font-weight:800; font-size:32px; background: linear-gradient(90deg,#D4A574,#8B5E34); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
</style>
""", unsafe_allow_html=True)

# --- FIX CRÍTICO: LIMPIAR TEXTO PARA WORD ---
def clean_text_for_word(text):
    """Elimina NULL bytes y caracteres de control que rompen docx"""
    if not text:
        return ""
    # Eliminar NULL bytes \x00
    text = text.replace('\x00', '')
    # Eliminar caracteres de control excepto \n, \r, \t
    # Mantener solo caracteres válidos XML: #x9 | #xA | #xD | #x20-#xD7FF...
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    # Eliminar caracteres no imprimibles raros
    text = ''.join(c for c in text if c.isprintable() or c in ['\n', '\r', '\t'])
    return text.strip()

def ocr_image_pil(image_pil):
    text = ""
    try:
        import pytesseract
        custom_config = r'--oem 3 --psm 6 -l spa+eng'
        text = pytesseract.image_to_string(image_pil, config=custom_config)
        text = clean_text_for_word(text)
        if len(text) > 20:
            return text
    except Exception as e:
        pass
    try:
        import easyocr
        if 'ocr_reader' not in st.session_state:
            with st.spinner("Cargando OCR (30s primera vez)..."):
                st.session_state.ocr_reader = easyocr.Reader(['es', 'en'], gpu=False)
        reader = st.session_state.ocr_reader
        results = reader.readtext(image_pil, detail=0, paragraph=True)
        text_easy = "\n".join(results)
        text_easy = clean_text_for_word(text_easy)
        if len(text_easy) > len(text):
            text = text_easy
    except Exception as e:
        pass
    return clean_text_for_word(text)

st.markdown('<div class="title">📸➡️📝 PDF con FOTOS a WORD - FIXED</div>', unsafe_allow_html=True)
st.caption("Error NULL bytes corregido")

col1, col2 = st.columns([1.3, 0.9])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    uploaded = st.file_uploader("Sube PDF con fotos", type=["pdf","png","jpg","jpeg"])
    
    if uploaded and st.button("🚀 CONVERTIR A WORD (FIXED)", type="primary", use_container_width=True):
        from docx import Document
        from docx.shared import Inches
        from PIL import Image
        
        doc = Document()
        doc.add_heading(f'Convertido: {uploaded.name}', 0)
        doc.add_paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Fix: NULL bytes eliminados")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        full_text_all = ""
        
        try:
            if uploaded.type in ["image/png", "image/jpeg", "image/jpg"]:
                image = Image.open(uploaded).convert("RGB")
                text = ocr_image_pil(image)
                text = clean_text_for_word(text) or "[No se detectó texto]"
                doc.add_heading("Texto extraído", 1)
                # FIX: siempre limpiar antes de add_paragraph
                doc.add_paragraph(clean_text_for_word(text)[:10000])
                full_text_all = text
                progress_bar.progress(1.0)
            else:
                import fitz
                pdf_data = uploaded.getvalue()
                doc_fitz = fitz.open(stream=pdf_data, filetype="pdf")
                total_pages = len(doc_fitz)
                
                for i in range(total_pages):
                    status_text.text(f"Página {i+1}/{total_pages}")
                    progress_bar.progress((i+1)/total_pages)
                    
                    page = doc_fitz[i]
                    text_digital = clean_text_for_word(page.get_text("text") or "")
                    
                    doc.add_heading(f"Página {i+1}", 2)
                    
                    if len(text_digital) > 100:
                        # Texto digital - limpiar por si tiene basura
                        safe_text = clean_text_for_word(text_digital)
                        # Dividir en chunks de 3000 para evitar párrafos gigantes que rompen WORD
                        for chunk in [safe_text[j:j+3000] for j in range(0, len(safe_text), 3000)]:
                            if chunk.strip():
                                doc.add_paragraph(chunk)
                        full_text_all += safe_text + "\n"
                    else:
                        # OCR
                        try:
                            pix = page.get_pixmap(dpi=300)
                            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                            text_ocr = ocr_image_pil(img)
                            text_ocr = clean_text_for_word(text_ocr)
                            if len(text_ocr) < 10:
                                text_ocr = f"[Página {i+1}: sin texto detectable]"
                            # FIX CRÍTICO: sanitizar antes de agregar
                            doc.add_paragraph(text_ocr[:10000])
                            full_text_all += text_ocr + "\n"
                        except Exception as e:
                            err_msg = clean_text_for_word(f"[Error OCR página {i+1}: {str(e)[:200]}]")
                            doc.add_paragraph(err_msg)
                
                doc_fitz.close()
            
            bio = BytesIO()
            doc.save(bio)
            st.session_state['word_file'] = bio.getvalue()
            st.session_state['full_text'] = clean_text_for_word(full_text_all)
            st.session_state['orig_name'] = uploaded.name
            status_text.text("✅ Conversión OK - NULL bytes eliminados")
            st.balloons()
            st.success("¡Corregido! Ya no dará error de XML")
            
        except Exception as e:
            st.error(f"Error: {e}")
            st.code(str(e))
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📥 Resultado")
    if 'word_file' in st.session_state:
        st.download_button("⬇️ DESCARGAR WORD FIXED", st.session_state['word_file'],
            file_name=f"{st.session_state.get('orig_name','doc').split('.')[0]}_FIXED.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary", use_container_width=True)
        st.text_area("Vista previa", st.session_state.get('full_text','')[:4000], height=400)
    else:
        st.info("Sube tu PDF con fotos. Este fix elimina los \\x00 y caracteres de control que rompían el WORD.")
    st.markdown('</div>', unsafe_allow_html=True)
