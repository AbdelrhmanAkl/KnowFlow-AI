from pathlib import Path

import pymupdf
from langchain_core.documents import Document


def load_pdf(file_path: str | Path) -> list[Document]:
    """
    Load a PDF file and convert each non-empty page
    into a LangChain Document.

    Args:
        file_path: Path to the PDF file.

    Returns:
        A list of LangChain Document objects, one per non-empty page.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        ValueError: If the provided file is not a PDF.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, got: {path.suffix}")

    documents: list[Document] = []

    with pymupdf.open(path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()

            if not text:
                continue

            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": path.name,
                        "file_path": str(path.resolve()),
                        "page": page_number,
                    },
                )
            )

    return documents
