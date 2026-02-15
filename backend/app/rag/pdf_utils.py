# app/rag/pdf_utils.py
import fitz  # PyMuPDF

def extract_text_from_pdf(path: str) -> str:
    doc = fitz.open(path)
    out = []

    for page in doc:
        txt = page.get_text("text") or ""
        out.append(txt)

    doc.close()
    text = "\n".join(out).strip()

    # If text extracted is too small, run OCR
    if len(text) < 80:
        try:
            import easyocr
            import numpy as np

            reader = easyocr.Reader(["en"])  # OCR English (best for PDFs)
            doc = fitz.open(path)
            ocr_out = []

            for i in range(len(doc)):
                page = doc[i]
                pix = page.get_pixmap(dpi=200)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                result = reader.readtext(img, detail=0)
                ocr_out.append(" ".join(result))

            doc.close()
            text = "\n".join(ocr_out).strip()
        except Exception as e:
            # OCR optional: if error, just return whatever we got
            return text

    return text
