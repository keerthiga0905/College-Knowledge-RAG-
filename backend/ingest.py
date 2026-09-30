import os
import sys
import argparse
import uuid
from pathlib import Path
from colorama import init, Fore, Style

# Ensure app is in python path
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from app.config import settings, ROOT_DIR
from app.database import SessionLocal, Base, engine
from app.models.document import Document
from app.services.document_processor import document_processor
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store

init(autoreset=True)

CATEGORIES = [
    "01_College_information",
    "02_Syllabus",
    "03_Academic_Calendar",
    "04_Lab_Manuals",
    "05_Fees_Placement_Funding"
]


def run_ingestion(reset: bool = False, dry_run: bool = False):
    print(f"\n{Fore.CYAN}{Style.BRIGHT}==================================================")
    print(f"{Fore.CYAN}{Style.BRIGHT}   College AI Knowledge Base - Document Ingestion")
    print(f"{Fore.CYAN}{Style.BRIGHT}==================================================\n")

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    provider = embedding_service.get_embedding_provider_name()
    print(
        f"{Fore.GREEN}[*] Active Embedding Engine: "
        f"{Style.BRIGHT}{provider}{Style.NORMAL}\n"
    )

    # Reset only when explicitly requested
    if reset and not dry_run:
        print(
            f"{Fore.YELLOW}[!] Resetting ChromaDB collection "
            f"and database document records..."
        )

        vector_store.clear()

        db.query(Document).delete()
        db.commit()

        print(
            f"{Fore.GREEN}[+] Cleared existing vector data "
            f"and records.\n"
        )

    root_path = Path(settings.DOCUMENTS_ROOT_DIR)

    print(
        f"{Fore.BLUE}[*] Searching for documents in: "
        f"{root_path}"
    )

    total_chunks = 0
    indexed_files = 0
    scanned_files = 0
    failed_files = 0
    skipped_files = 0

    all_found_files = []

    # Find all supported documents
    for category in CATEGORIES:

        cat_path = root_path / category

        if not cat_path.exists():
            print(
                f"{Fore.YELLOW}[!] Category folder not found: "
                f"{category}"
            )
            continue

        files_in_cat = [
            f
            for f in cat_path.rglob("*")
            if f.is_file()
            and f.suffix.lower() in [".pdf", ".docx", ".doc"]
        ]

        all_found_files.extend(
            [(f, category) for f in files_in_cat]
        )

    print(
        f"{Fore.GREEN}[+] Found {len(all_found_files)} "
        f"documents across {len(CATEGORIES)} categories.\n"
    )

    # Process every document
    for file_path, category in all_found_files:

        filename = file_path.name
        rel_path = file_path.relative_to(root_path)
        file_size_kb = file_path.stat().st_size / 1024

        print(
            f"{Fore.WHITE}Processing: "
            f"{Fore.YELLOW}{rel_path} "
            f"{Fore.LIGHTBLACK_EX}({file_size_kb:.1f} KB)...",
            end=" ",
            flush=True
        )

        sys.stdout.flush()

        # Check existing database record
        doc_record = db.query(Document).filter(
            Document.filename == filename,
            Document.category == category
        ).first()

        # ---------------------------------------------------------
        # IMPORTANT:
        # Skip files that were already successfully processed.
        # This prevents OCR and embedding from running again.
        # ---------------------------------------------------------
        if (
            doc_record
            and doc_record.status == "processed"
            and not dry_run
        ):
            print(
                f"{Fore.GREEN}[SKIP] Already indexed."
            )
            skipped_files += 1
            continue

        # Create database record if it does not exist
        if not doc_record and not dry_run:

            doc_record = Document(
                document_id=str(uuid.uuid4()),
                filename=filename,
                category=category,
                filepath=str(file_path.resolve()),
                file_size=file_path.stat().st_size,
                status="pending"
            )

            db.add(doc_record)
            db.commit()
            db.refresh(doc_record)

        try:

            # Extract and process document
            chunks = document_processor.process_file(
                str(file_path),
                category
            )

            num_chunks = len(chunks)

            # Dry run
            if dry_run:

                if num_chunks > 0:

                    print(
                        f"{Fore.GREEN}[+] [DRY RUN] "
                        f"{num_chunks} chunks extracted."
                    )

                    indexed_files += 1

                else:

                    print(
                        f"{Fore.YELLOW}[!] [DRY RUN] "
                        f"Scanned image PDF "
                        f"(0 raw text chunks)."
                    )

                    scanned_files += 1

                total_chunks += num_chunks

                continue

            # No chunks found
            if num_chunks == 0:

                print(
                    f"{Fore.YELLOW}[!] Scanned image PDF "
                    f"(0 raw text chunks)."
                )

                if doc_record:

                    doc_record.status = "scanned_image_no_ocr"
                    doc_record.chunk_count = 0
                    doc_record.error_message = (
                        "Scanned PDF "
                        "(image-only pages, requires OCR engine)"
                    )

                    db.commit()

                scanned_files += 1

                continue

            # -----------------------------------------------------
            # Generate embeddings
            # -----------------------------------------------------

            texts = [
                c.text
                for c in chunks
            ]

            embeddings = (
                embedding_service.get_embeddings_batch(
                    texts
                )
            )

            # -----------------------------------------------------
            # Store vectors in ChromaDB
            # -----------------------------------------------------

            vector_store.add_chunks(
                chunks,
                embeddings
            )

            # -----------------------------------------------------
            # Update database record
            # -----------------------------------------------------

            if doc_record:

                doc_record.chunk_count = num_chunks
                doc_record.status = "processed"
                doc_record.error_message = None

                db.commit()

            print(
                f"{Fore.GREEN}[+] Indexed "
                f"{num_chunks} chunks into ChromaDB.",
                flush=True
            )

            total_chunks += num_chunks
            indexed_files += 1

        except KeyboardInterrupt:

            print(
                f"\n{Fore.YELLOW}[!] Ingestion interrupted by user."
            )

            if doc_record and not dry_run:

                doc_record.status = "pending"
                doc_record.error_message = (
                    "Ingestion interrupted by user"
                )

                db.commit()

            db.close()

            return

        except Exception as e:

            print(
                f"{Fore.RED}[X] Error: {e}"
            )

            if doc_record and not dry_run:

                doc_record.status = "failed"
                doc_record.error_message = str(e)

                db.commit()

            failed_files += 1

    db.close()

    # -------------------------------------------------------------
    # Final summary
    # -------------------------------------------------------------

    print(
        f"\n{Fore.CYAN}{Style.BRIGHT}=================================================="
    )

    print(
        f"{Fore.CYAN}{Style.BRIGHT}               Ingestion Summary"
    )

    print(
        f"{Fore.CYAN}{Style.BRIGHT}=================================================="
    )

    print(
        f"{Fore.WHITE}Total Files Discovered:       "
        f"{len(all_found_files)}"
    )

    print(
        f"{Fore.GREEN}Text Files Indexed in Chroma: "
        f"{indexed_files}"
    )

    print(
        f"{Fore.GREEN}Already Indexed / Skipped:    "
        f"{skipped_files}"
    )

    print(
        f"{Fore.YELLOW}Scanned Image Files Flagged:  "
        f"{scanned_files}"
    )

    if failed_files > 0:

        print(
            f"{Fore.RED}Failed to Process:            "
            f"{failed_files}"
        )

    print(
        f"{Fore.CYAN}Total Real Chunks Generated:  "
        f"{total_chunks}"
    )

    if not dry_run:

        print(
            f"{Fore.GREEN}ChromaDB Total Stored Count:  "
            f"{vector_store.count()} chunks"
        )

    print(
        f"{Fore.CYAN}{Style.BRIGHT}==================================================\n"
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Ingest college documents into "
            "ChromaDB vector store."
        )
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear vector database before ingesting."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Extract and chunk without embedding "
            "or saving."
        )
    )

    args = parser.parse_args()

    run_ingestion(
        reset=args.reset,
        dry_run=args.dry_run
    )