from pathlib import Path

from langchain_core.documents import Document

from src.generation.llm import create_llm
from src.memory.conversation_memory import ConversationMemory
from src.retrieval.query_rewriter import rewrite_query
from src.retrieval.retriever import retrieve_documents


DEFAULT_TOP_K = 4
DEFAULT_KNOWLEDGE_BASE_PATH = "data/knowledge_base"


def build_context(documents: list[Document]) -> str:
    """
    Combine retrieved documents into a single context string.
    """

    if not documents:
        return ""

    context_parts = []

    for index, document in enumerate(documents, start=1):
        source = document.metadata.get("source", "unknown")
        page = document.metadata.get("page", "unknown")
        row = document.metadata.get("row", "unknown")

        location = f"Page {page}"

        if page == "unknown" and row != "unknown":
            location = f"Row {row}"

        context_parts.append(
            f"[Source {index} | {source} | {location}]\n"
            f"{document.page_content}"
        )

    return "\n\n".join(context_parts)


def build_memory_context(
    memory: ConversationMemory | None,
) -> str:
    """
    Convert conversation history into a readable context string.
    """

    if memory is None:
        return ""

    messages = memory.get_messages()

    if not messages:
        return ""

    history_parts = []

    for message in messages:
        role = message["role"].capitalize()
        content = message["content"]

        history_parts.append(
            f"{role}: {content}"
        )

    return "\n".join(history_parts)


def generate_answer(
    vector_store,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    memory: ConversationMemory | None = None,
) -> dict:
    """
    Run the complete RAG pipeline.

    Flow:
        User Query
        -> Contextual Query Rewriting
        -> FAISS Retrieval
        -> Conversation Memory
        -> Gemini Generation
        -> Memory Update

    Args:
        vector_store: Loaded FAISS knowledge base.
        query: User question.
        top_k: Number of documents to retrieve.
        memory: Optional conversation memory.

    Returns:
        Dictionary containing:
            - answer
            - query
            - documents
    """

    if vector_store is None:
        raise ValueError(
            "A valid knowledge base is required."
        )

    if not query or not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than 0."
        )

    # Rewrite the query using conversation history
    # so follow-up questions can be resolved correctly.
    rewritten_query = rewrite_query(
        query=query,
        memory=memory,
    )

    documents = retrieve_documents(
        vector_store=vector_store,
        query=rewritten_query,
        k=top_k,
    )

    context = build_context(documents)
    conversation_history = build_memory_context(memory)

    if not context:
        answer = (
            "I could not find relevant information "
            "in the provided documents."
        )

        if memory is not None:
            memory.add_user_message(query)
            memory.add_assistant_message(answer)

        return {
            "answer": answer,
            "query": rewritten_query,
            "documents": [],
        }

    prompt = f"""
You are KnowFlow-AI, a document question-answering assistant.

Your task is to answer the user's question using ONLY
the provided document context.

Rules:
- Do not use outside knowledge.
- Do not invent facts.
- If the answer is not supported by the provided documents,
  clearly say that the information was not found in the
  provided documents.
- Be accurate and concise.
- Use the conversation history only to understand references,
  follow-up questions, and context.
- The retrieved document context is the authoritative source
  for factual answers.

Conversation History:
{conversation_history if conversation_history else "No previous conversation."}

Document Context:
{context}

User Question:
{rewritten_query}
"""

    client = create_llm()

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    answer = response.text.strip()

    if memory is not None:
        memory.add_user_message(query)
        memory.add_assistant_message(answer)

    return {
        "answer": answer,
        "query": rewritten_query,
        "documents": documents,
    }


def generate_answer_from_saved_knowledge_base(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    memory: ConversationMemory | None = None,
    knowledge_base_path: str | Path = DEFAULT_KNOWLEDGE_BASE_PATH,
) -> dict:
    """
    Run RAG using a previously saved FAISS knowledge base.

    This is the production-style entry point used after
    the knowledge base has already been built and persisted.

    Flow:
        Saved FAISS
        -> Load
        -> Contextual Query Rewriting
        -> Retrieval
        -> Gemini
        -> Conversation Memory
        -> Answer
    """

    from src.knowledge_base import load_knowledge_base

    knowledge_base = load_knowledge_base(
        knowledge_base_path
    )

    return generate_answer(
        vector_store=knowledge_base,
        query=query,
        top_k=top_k,
        memory=memory,
    )