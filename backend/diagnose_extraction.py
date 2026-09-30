import sys
from pathlib import Path
import pymupdf as fitz
from pypdf import PdfReader

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

root = Path(__file__).resolve().parent.parent

categories = [
    "01_College_information",
    "02_Syllabus",
    "03_Academic_Calendar",
    "04_Lab_Manuals",
    "05_Fees_Placement_Funding"
]

print("=" * 70)
print("     DETAILED EXTRACTION DIAGNOSIS ACROSS ALL 63 FILES")
print("=" * 70)

zero_text_files = []
text_files = []

for cat in categories:
    cat_path = root / cat
    if not cat_path.exists():
        continue
    for f in cat_path.rglob("*"):
        if f.is_file() and f.suffix.lower() in [".pdf", ".docx", ".doc"]:
            if f.suffix.lower() == ".pdf":
                try:
                    doc = fitz.open(f)
                    total_pages = len(doc)
                    full_text = ""
                    total_images = 0
                    for page in doc:
                        full_text += page.get_text()
                        total_images += len(page.get_images())
                    
                    cleaned_len = len(full_text.strip())
                    if cleaned_len == 0:
                        zero_text_files.append((f, cat, total_pages, total_images))
                    else:
                        text_files.append((f, cat, total_pages, cleaned_len))
                except Exception as e:
                    print(f"[ERROR reading {f.name}]: {e}")

print(f"\n[SUMMARY]")
print(f"Files WITH standard extractable text: {len(text_files)}")
print(f"Files with ZERO extractable text (Scanned images): {len(zero_text_files)}")

print("\n--- SAMPLE SCANNED (ZERO-TEXT) FILES ---")
for f, cat, pages, imgs in zero_text_files[:10]:
    print(f"File: {f.name} | Cat: {cat} | Pages: {pages} | Total Images: {imgs}")
