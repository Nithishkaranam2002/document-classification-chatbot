import os
from pypdf import PdfReader
from docx import Document

# Optional OCR imports (only used if installed)
try:
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

def load_text_from_path(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        txt = _pdf_to_text(path)
        if len(txt.strip()) < 200 and OCR_AVAILABLE:
            ocr_txt = _pdf_to_text_ocr(path)
            if len(ocr_txt.strip()) > len(txt.strip()):
                return ocr_txt
        return txt
    if ext in (".docx", ".doc"):
        return _docx_to_text(path)
    if ext in (".txt", ".md"):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    if ext in (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff") and OCR_AVAILABLE:
        return _image_ocr(path)
    raise ValueError(f"Unsupported file type or OCR not available: {ext}")

def _pdf_to_text(path: str) -> str:
    reader = PdfReader(path)
    parts = []
    for p in reader.pages:
        parts.append(p.extract_text() or "")
    return "\n".join(parts)

def _docx_to_text(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def _pdf_to_text_ocr(path: str, dpi: int = 300, lang: str = "eng") -> str:
    pages = convert_from_path(path, dpi=dpi)
    out = []
    for img in pages:
        out.append(pytesseract.image_to_string(img, lang=lang))
    return "\n".join(out)

def _image_ocr(path: str, lang: str = "eng") -> str:
    img = Image.open(path)
    return pytesseract.image_to_string(img, lang=lang)
