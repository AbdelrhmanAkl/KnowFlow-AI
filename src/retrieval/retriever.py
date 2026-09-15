from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS


def retrieve_documents(
    vector_store: FAISS,
    query: str,
    k: int = 4,
) -> list[Document]:
    """
    Retrieve the most relevant documents for a query.

    Args:
        vector_store: FAISS vector store.
        query: User query.
        k: Number of documents to retrieve.

    Returns:
        A list of relevant documents.

    Raises:
        ValueError: If the query is empty or k is invalid.
    """

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if k <= 0:
        raise ValueError("k must be greater than 0")

    return vector_store.similarity_search(
        query.strip(),
        k=k,
    )
