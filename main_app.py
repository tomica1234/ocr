import streamlit as st
import pyocr
import pyocr.builders
from PIL import Image
import fitz  # PyMuPDF
from PyPDF2 import PdfReader
from io import BytesIO

# Streamlitアプリのタイトル
st.title('I LOVE OCR')

# 利用可能なOCRツールを取得
tools = pyocr.get_available_tools()
tool = tools[0] if tools else None

if not tool:
    st.error("No OCR tool found")
else:
    lang_options = ['fra', 'eng', 'jpn', 'deu', 'lat', 'ita']
    lang = st.selectbox('Select language', lang_options, index=lang_options.index('fra'))

    def process_image(image_file, lang):
        with Image.open(image_file) as img, BytesIO() as output:
            img.seek(0)
            for i in range(getattr(img, 'n_frames', 1)):
                img.seek(i)
                text = tool.image_to_string(
                    img,
                    lang=lang,
                    builder=pyocr.builders.TextBuilder(tesseract_layout=6)
                )
                output.write(f"--- Page {i+1} ---\n{text}\n\n".encode('utf-8'))
            output.seek(0)
            return output.getvalue(), image_file.name.split('.')[0] + '.txt'

    def process_pdf_text_based(pdf_bytes, file_name):
        reader = PdfReader(pdf_bytes)
        num_pages = len(reader.pages)
        with BytesIO() as output:
            for i in range(num_pages):
                page = reader.pages[i]
                text = page.extract_text()
                if text:
                    output.write(f"--- Page {i+1} ---\n{text}\n\n".encode('utf-8'))
            output.seek(0)
            return output.getvalue(), file_name.split('.')[0] + '.txt'

    def process_pdf_image_based(pdf_bytes, lang, file_name):
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc, BytesIO() as output:
            for i, page in enumerate(doc):
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                text = tool.image_to_string(
                    img,
                    lang=lang,
                    builder=pyocr.builders.TextBuilder(tesseract_layout=6)
                )
                output.write(f"--- Page {i+1} ---\n{text}\n\n".encode('utf-8'))
            output.seek(0)
            return output.getvalue(), file_name.split('.')[0] + '.txt'

    def is_text_based_pdf(doc):
        for page in doc:
            text = page.get_text()
            if text.strip():
                return True
        return False
    

    uploaded_file = st.file_uploader("Upload file here (PDF TIFF JPG HEIF)", type=['pdf', 'tif', 'tiff','jpg','jpeg','heif'])

    if uploaded_file:
        file_name = uploaded_file.name
        file_bytes = uploaded_file.getvalue()

        if uploaded_file.type == "application/pdf":
            with fitz.open(stream=BytesIO(file_bytes), filetype="pdf") as doc:
                if is_text_based_pdf(doc):
                    text_data, file_name = process_pdf_text_based(BytesIO(file_bytes), file_name)
                else:
                    text_data, file_name = process_pdf_image_based(BytesIO(file_bytes), lang, file_name)
            st.download_button(
                label="Download text",
                data=text_data,
                file_name=file_name,
                mime='text/plain'
            )
            st.write(text_data.decode('utf-8'))
        elif uploaded_file.type in ["image/tiff", "image/tif", "image/jpg", "image/jpeg", "image/heif"]:
            text_data, file_name = process_image(uploaded_file, lang)
            st.download_button(
                label="Download text",
                data=text_data,
                file_name=file_name,
                mime='text/plain'
            )
            st.write(text_data.decode('utf-8'))
        else:
            st.error("This file format is not supported")
