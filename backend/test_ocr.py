import sys
from pathlib import Path
import pymupdf as fitz

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sample_path = Path("01_College_information") / "Citizen's-Charter.pdf"
doc = fitz.open(sample_path)
print("Pages in sample:", len(doc))
try:
    tp = doc[0].get_textpage_ocr(language="eng")
    text = doc[0].get_text(textpage=tp)
    print("OCR extracted length:", len(text.strip()))
    print("OCR extracted snippet:\n", text[:300])
except Exception as e:
    print("OCR error:", e)
