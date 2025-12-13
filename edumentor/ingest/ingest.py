from pathlib import Path
from typing import List
import fitz
from tqdm import tqdm
from edumentor.config import settings
from edumentor.retrieval.vectorstore import VectorStore, build_doc_entries


def ingest_pdf(pdf_path: Path, collection_name: str = "edumentor") -> int:
    vs = VectorStore(collection_name)
    doc = fitz.open(str(pdf_path))
    total = 0
    for page_index in tqdm(range(doc.page_count)):
        page = doc.load_page(page_index)
        text = page.get_text()
        if not text.strip():
            continue
        docs = build_doc_entries(pdf_path, page_index + 1, text, pdf_path.stem)
        total += vs.add_documents(docs)
    return total


def ingest_folder(folder: Path, pattern: str = "*.pdf", collection_name: str = "edumentor") -> int:
    count = 0
    for p in folder.glob(pattern):
        count += ingest_pdf(p, collection_name)
    return count


def save_uploaded(name: str, data: bytes) -> Path:
    target = settings.docs_dir / name
    with open(target, "wb") as f:
        f.write(data)
    return target


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        sys.exit(1)
    path = Path(sys.argv[1])
    if path.is_file():
        ingest_pdf(path)
    elif path.is_dir():
        ingest_folder(path)
