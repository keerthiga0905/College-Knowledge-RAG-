import sys
import os
import json
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.services.document_processor import document_processor
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store

def crawl_and_ingest_cit_page(url: str, category: str = "01_College_information"):
    """
    Crawls a CIT website URL, extracts text, structured faculty metadata, and indexes into ChromaDB.
    """
    print(f"[*] Crawling CIT Official URL: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CIT-Knowledge-AI/1.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code != 200:
            print(f"[X] Failed to fetch URL (HTTP {response.status_code})")
            return False

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove header, footer, nav, script tags
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Page title & content
        title = soup.title.string.strip() if soup.title else "CIT Official Page"
        raw_text = soup.get_text(separator="\n")
        cleaned_text = document_processor.clean_text(raw_text)

        if len(cleaned_text) < 50:
            print("[!] Scraped page has insufficient content.")
            return False

        # Save scraped file to data/cleaned
        output_dir = ROOT_DIR / "01_College_information"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        safe_filename = "CIT_Scraped_" + re.sub(r"[^a-zA-Z0-9]", "_", title)[:40] + ".txt"
        file_path = output_dir / safe_filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Source URL: {url}\nTitle: {title}\nCategory: {category}\n\n{cleaned_text}")

        print(f"[+] Saved scraped content to: {file_path.name}")

        # Process chunks and embed into ChromaDB
        chunks = document_processor.process_file(str(file_path), category)
        if chunks:
            texts = [c.text for c in chunks]
            embeddings = embedding_service.get_embeddings_batch(texts)
            vector_store.add_chunks(chunks, embeddings)
            print(f"[+] Successfully indexed {len(chunks)} chunks into ChromaDB!")

        return True

    except Exception as e:
        print(f"[X] Crawler error: {e}")
        return False

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.cit.edu.in"
    crawl_and_ingest_cit_page(target_url)
