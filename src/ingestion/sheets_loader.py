from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd
from langchain_core.documents import Document


def _dataframe_to_documents(
    dataframe: pd.DataFrame,
    source: str,
    file_path: str | None = None,
) -> list[Document]:
    """
    Convert dataframe rows into LangChain Documents.
    """

    if dataframe.empty:
        raise ValueError(
            f"Data source contains no rows: {source}"
        )

    documents: list[Document] = []

    for row_number, row in dataframe.iterrows():
        content_parts = []

        for column, value in row.items():
            if pd.isna(value):
                continue

            content_parts.append(
                f"{column}: {value}"
            )

        if not content_parts:
            continue

        metadata = {
            "source": source,
            "row": int(row_number) + 2,
        }

        if file_path:
            metadata["file_path"] = file_path

        documents.append(
            Document(
                page_content="\n".join(content_parts),
                metadata=metadata,
            )
        )

    return documents


def load_sheet(
    file_path: str | Path,
) -> list[Document]:
    """
    Load a local spreadsheet file and convert each row
    into a LangChain Document.

    Supported formats:
        - .csv
        - .xlsx
        - .xls
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Spreadsheet file not found: {path}"
        )

    suffix = path.suffix.lower()

    if suffix == ".csv":
        dataframe = pd.read_csv(path)

    elif suffix in {".xlsx", ".xls"}:
        dataframe = pd.read_excel(path)

    else:
        raise ValueError(
            f"Unsupported spreadsheet format: {suffix}"
        )

    return _dataframe_to_documents(
        dataframe=dataframe,
        source=path.name,
        file_path=str(path.resolve()),
    )


def load_google_sheet(
    sheet_url: str,
) -> list[Document]:
    """
    Load a Google Sheet using its Google Sheets URL.

    The Google Sheet must be accessible for reading,
    for example through a published/public sharing configuration.

    Supported URL format:

        https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit#gid=0

    The function converts the URL into Google's CSV export
    endpoint and loads the sheet using pandas.
    """

    if not sheet_url or not sheet_url.strip():
        raise ValueError(
            "Google Sheets URL cannot be empty."
        )

    sheet_url = sheet_url.strip()

    parsed_url = urlparse(sheet_url)

    if parsed_url.netloc not in {
        "docs.google.com",
        "docs.googleusercontent.com",
    }:
        raise ValueError(
            "Invalid Google Sheets URL."
        )

    path_parts = parsed_url.path.strip("/").split("/")

    if (
        len(path_parts) < 3
        or path_parts[0] != "spreadsheets"
        or path_parts[1] != "d"
    ):
        raise ValueError(
            "Invalid Google Sheets URL format."
        )

    spreadsheet_id = path_parts[2]

    query_params = parse_qs(parsed_url.query)

    gid = query_params.get("gid", [None])[0]

    if gid is None and parsed_url.fragment.startswith("gid="):
        gid = parsed_url.fragment.split("=", 1)[1]

    export_url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{spreadsheet_id}/export?format=csv"
    )

    if gid:
        export_url += f"&gid={gid}"

    try:
        dataframe = pd.read_csv(export_url)

    except Exception as exc:
        raise ValueError(
            "Could not read the Google Sheet. "
            "Make sure the sheet is publicly accessible "
            "or published for web access."
        ) from exc

    return _dataframe_to_documents(
        dataframe=dataframe,
        source=f"google_sheet:{spreadsheet_id}",
    )