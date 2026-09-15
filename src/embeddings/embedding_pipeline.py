from langchain_huggingface import HuggingFaceEmbeddings


DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def create_embeddings(
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> HuggingFaceEmbeddings:
    """
    Create and return the Hugging Face embedding model.

    Args:
        model_name: Hugging Face embedding model name.

    Returns:
        Configured HuggingFaceEmbeddings instance.
    """

    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
