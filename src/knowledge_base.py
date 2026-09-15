from pathlib import Path

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from src.embeddings.embedding_pipeline import create_embeddings
from src.ingestion.loader import load_documents
from src.ingestion.text_splitter import split_documents
from src.retrieval.vector_store import build_vector_store


DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150


def load_and_prepare_source(
    source: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Document]:
    """
    Load a supported knowledge source and split it into chunks.

    Supported sources:
        - PDF
        - CSV
        - XLSX
        - XLS
        - Google Sheets URL
    """

    documents = load_documents(source)

    if not documents:
        raise ValueError(
            f"No documents were loaded from source: {source}"
        )

    chunks = split_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    if not chunks:
        raise ValueError(
            f"No chunks were created from source: {source}"
        )

    return chunks


def build_knowledge_base(
    sources: list[str | Path],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> FAISS:
    """
    Build one FAISS knowledge base from multiple sources.

    Pipeline:
        Sources
        -> Unified Loader
        -> Chunking
        -> Embeddings
        -> Single FAISS index

    Args:
        sources: List of local files or Google Sheets URLs.
        chunk_size: Maximum size of each chunk.
        chunk_overlap: Number of overlapping characters.

    Returns:
        A FAISS vector store containing all knowledge sources.
    """

    if not sources:
        raise ValueError(
            "At least one knowledge source is required."
        )

    all_chunks: list[Document] = []

    for source in sources:
        chunks = load_and_prepare_source(
            source=source,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError(
            "No chunks were created from the provided sources."
        )

    embeddings = create_embeddings()

    return build_vector_store(
        documents=all_chunks,
        embeddings=embeddings,
    )


def save_knowledge_base(
    knowledge_base: FAISS,
    directory: str | Path,
) -> None:
    """
    Save the FAISS knowledge base locally.
    """

    path = Path(directory)

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    knowledge_base.save_local(str(path))


def load_knowledge_base(
    directory: str | Path,
) -> FAISS:
    """
    Load a previously saved FAISS knowledge base.
    """

    path = Path(directory)

    if not path.exists():
        raise FileNotFoundError(
            f"Knowledge base directory not found: {path}"
        )

    embeddings = create_embeddings()

    return FAISS.load_local(
        str(path),
        embeddings,
        allow_dangerous_deserialization=True,
    )