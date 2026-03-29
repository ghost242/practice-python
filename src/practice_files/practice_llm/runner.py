from __future__ import annotations

import logging

from pathlib import Path

from practice_files.practice_llm.rag.load_pdf import (
    build_pdf,
)


logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    for name in ("httpx", "httpcore", "urllib3", "chromadb"):
        logging.getLogger(name).setLevel(logging.WARNING)


if __name__ == "__main__":
    configure_logging()
    build_pdf(
        pdf_path=Path("./resources/Introduction_to_Philosophy.pdf"),
        page_range=(16, 412),
        provider_url="http://ollama:11434",
        persist_dir="./philosophy_db",
        collection_name="intro_to_philosophy",
    )
