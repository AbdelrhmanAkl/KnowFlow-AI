from pathlib import Path

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from src.embeddings.embedding_pipeline import create_embeddings
from src.ingestion.loader import load_documents
from src.ingestion.text_splitter import split_documents


def build_vector_store(
    documents: list[Document],
    embeddings: HuggingFaceEmbeddings,
) -> FAISS:
    """
    Build a FAISS vector store from LangChain documents.

    Args:
        documents: Documents to embed and index.
        embeddings: Configured embedding model.

    Returns:
        A FAISS vector store containing the documents.

    Raises:
        ValueError: If no documents are provided.
    """

    if not documents:
        raise ValueError(
            "Cannot build a vector store from empty documents."
        )

    return FAISS.from_documents(
        documents=documents,
        embedding=embeddings,
    )


def save_vector_store(
    vector_store: FAISS,
    directory: str | Path,
) -> None:
    """
    Save a FAISS vector store locally.

    Args:
        vector_store: FAISS vector store to save.
        directory: Target directory.
    """

    path = Path(directory)

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    vector_store.save_local(str(path))


def load_vector_store(
    directory: str | Path,
    embeddings: HuggingFaceEmbeddings,
) -> FAISS:
    """
    Load a previously saved FAISS vector store.

    Args:
        directory: Directory containing the FAISS index.
        embeddings: Same embedding model used to create the index.

    Returns:
        Loaded FAISS vector store.

    Raises:
        FileNotFoundError: If the vector store directory does not exist.
    """

    path = Path(directory)

    if not path.exists():
        raise FileNotFoundError(
            f"Vector store directory not found: {path}"
        )

    return FAISS.load_local(
        str(path),
        embeddings,
        allow_dangerous_deserialization=True,
    )


def build_vector_store_from_file(
    file_path: str | Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
    embedding_model: str | None = None,
) -> FAISS:
    """
    Build a FAISS vector store directly from a supported file.

    Pipeline:
        File
        -> Unified Loader
        -> Chunking
        -> Embeddings
        -> FAISS

    Args:
        file_path: Path to a supported file.
        chunk_size: Maximum size of each text chunk.
        chunk_overlap: Number of overlapping characters between chunks.
        embedding_model: Optional Hugging Face embedding model name.

    Returns:
        A FAISS vector store containing the processed file content.

    Raises:
        ValueError: If no documents or chunks are created.
    """

    documents = load_documents(file_path)

    if not documents:
        raise ValueError(
            f"No documents were loaded from: {file_path}"
        )

    chunks = split_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    if not chunks:
        raise ValueError(
            f"No chunks were created from: {file_path}"
        )

    if embedding_model:
        embeddings = create_embeddings(
            model_name=embedding_model,
        )
    else:
        embeddings = create_embeddings()

    return build_vector_store(
        documents=chunks,
        embeddings=embeddings,
    )