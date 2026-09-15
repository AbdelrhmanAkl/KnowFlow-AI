from pathlib import Path
from urllib.parse import urlparse

from langchain_core.documents import Document

from src.ingestion.pdf_loader import load_pdf
from src.ingestion.sheets_loader import load_google_sheet
from src.ingestion.sheets_loader import load_sheet


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".csv",
    ".xlsx",
    ".xls",
}


def load_documents(
    file_path: str | Path,
) -> list[Document]:
    """
    Load documents from a supported local file or Google Sheets URL.

    Supported sources:
        - PDF
        - CSV
        - XLSX
        - XLS
        - Google Sheets URL
    """

    source = str(file_path).strip()

    if not source:
        raise ValueError(
            "File path or source URL cannot be empty."
        )

    parsed_url = urlparse(source)

    if parsed_url.scheme in {"http", "https"}:
        if parsed_url.netloc not in {
            "docs.google.com",
            "docs.googleusercontent.com",
        }:
            raise ValueError(
                "Unsupported URL source. "
                "Only Google Sheets URLs are supported."
            )

        return load_google_sheet(source)

    path = Path(source)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format: {suffix}"
        )

    if suffix == ".pdf":
        return load_pdf(path)

    return load_sheet(path)